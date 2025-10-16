mod cabernet;
mod error;
mod ue;
use pyo3::prelude::*;

pub use cabernet::Cabernet;

/// The Python Wrapper of the cabernet module implemented in Rust.
#[pymodule]
fn layer3(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<cabernet::Cabernet>()
}
