// ABOUTME: PyO3 bindings exposing the vacant Rust engine to Python as `vacant._core`.
// ABOUTME: Surface: load_rules(), check_many(), DiskCache. Lockstep-versioned with vacant.
use std::path::PathBuf;
use std::str::FromStr;
use std::sync::{OnceLock, RwLock};
use std::time::Duration;

use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use vacant::{check_many as core_check_many, CheckResult, DiskCache, DnsClient, RuleSet};

static RULES: RwLock<Option<RuleSet>> = RwLock::new(None);
static DNS: OnceLock<DnsClient> = OnceLock::new();

fn dns_client(timeout: Duration) -> PyResult<&'static DnsClient> {
    if let Some(client) = DNS.get() {
        return Ok(client);
    }
    let client = DnsClient::new(timeout).map_err(|e| PyRuntimeError::new_err(format!("{e}")))?;
    let _ = DNS.set(client);
    Ok(DNS.get().expect("DNS just set"))
}

#[pyfunction]
fn load_rules(path: PathBuf) -> PyResult<()> {
    let text = std::fs::read_to_string(&path)
        .map_err(|e| PyValueError::new_err(format!("read {}: {e}", path.display())))?;
    let rs = RuleSet::from_str(&text).map_err(|e| PyValueError::new_err(format!("{e}")))?;
    let mut guard = RULES
        .write()
        .map_err(|_| PyRuntimeError::new_err("rules lock poisoned"))?;
    *guard = Some(rs);
    Ok(())
}

#[pyfunction]
#[pyo3(signature = (domains, concurrency=64, timeout=4.0, cache=None, cache_ttl=86_400.0))]
fn check_many(
    py: Python<'_>,
    domains: Vec<String>,
    concurrency: usize,
    timeout: f64,
    cache: Option<&PyDiskCache>,
    cache_ttl: f64,
) -> PyResult<Py<PyList>> {
    let dur = Duration::from_secs_f64(timeout.max(0.05));
    let dns = dns_client(dur)?;
    let cache_ref = cache.map(|c| &c.inner);

    let guard = RULES
        .read()
        .map_err(|_| PyRuntimeError::new_err("rules lock poisoned"))?;
    let rules = guard
        .as_ref()
        .ok_or_else(|| PyRuntimeError::new_err("rules not loaded; call load_rules() first"))?;

    let results: Vec<CheckResult> = py.allow_threads(|| {
        core_check_many(
            rules,
            dns,
            cache_ref,
            &domains,
            cache_ttl as i64,
            concurrency,
        )
    });

    let list = PyList::empty_bound(py);
    for r in results {
        let dict = PyDict::new_bound(py);
        dict.set_item("input", r.input)?;
        dict.set_item("domain", r.domain)?;
        dict.set_item("zone", r.zone)?;
        dict.set_item("status", r.status.as_str())?;
        dict.set_item("detail", r.detail)?;
        dict.set_item("from_cache", r.from_cache)?;
        list.append(dict)?;
    }
    Ok(list.unbind())
}

#[pyclass(name = "DiskCache")]
struct PyDiskCache {
    inner: DiskCache,
}

#[pymethods]
impl PyDiskCache {
    #[new]
    #[pyo3(signature = (path=None))]
    fn new(path: Option<PathBuf>) -> PyResult<Self> {
        let resolved = path.unwrap_or_else(DiskCache::default_path);
        let inner =
            DiskCache::open(&resolved).map_err(|e| PyValueError::new_err(format!("{e}")))?;
        Ok(Self { inner })
    }

    #[staticmethod]
    fn default_path() -> String {
        DiskCache::default_path().to_string_lossy().into_owned()
    }

    fn get<'py>(&self, py: Python<'py>, domain: &str, ttl: f64) -> PyResult<Option<Py<PyDict>>> {
        let row = self
            .inner
            .get(domain, ttl as i64)
            .map_err(|e| PyValueError::new_err(format!("{e}")))?;
        let Some(r) = row else { return Ok(None) };
        let dict = PyDict::new_bound(py);
        dict.set_item("domain", r.domain)?;
        dict.set_item("zone", r.zone)?;
        dict.set_item("status", r.status)?;
        dict.set_item("detail", r.detail)?;
        dict.set_item("checked_at", r.checked_at)?;
        Ok(Some(dict.unbind()))
    }

    fn put(&self, domain: &str, zone: &str, status: &str, detail: &str) -> PyResult<()> {
        self.inner
            .put(domain, zone, status, detail)
            .map_err(|e| PyValueError::new_err(format!("{e}")))
    }
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyDiskCache>()?;
    m.add_function(wrap_pyfunction!(load_rules, m)?)?;
    m.add_function(wrap_pyfunction!(check_many, m)?)?;
    Ok(())
}
