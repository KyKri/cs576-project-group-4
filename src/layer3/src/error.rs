use pyo3::{exceptions::PyValueError, PyErr};
use thiserror::Error;

pub type Result<T> = std::result::Result<T, CabernetError>;

#[derive(Error, Debug)]
pub enum CabernetError {
    #[error("IO Error happened: {0}")]
    IOError(#[from] std::io::Error),
}

impl From<CabernetError> for PyErr {
    fn from(value: CabernetError) -> Self {
        PyValueError::new_err(value.to_string())
    }
}
