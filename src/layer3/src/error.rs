use etherparse::err::ipv4::HeaderSliceError;
use pyo3::{exceptions::PyValueError, PyErr};
use thiserror::Error;

pub type Result<T> = std::result::Result<T, CabernetError>;

#[derive(Error, Debug)]
pub enum CabernetError {
    #[error("IO Error happened: {0}")]
    IOError(#[from] std::io::Error),

    #[error("requested ip is not assigned to any UE in the network")]
    IPNotAssignedError,

    #[error("failed to parse ipv4 header: {0}")]
    Ipv4HeaderParseError(#[from] HeaderSliceError),
}

impl From<CabernetError> for PyErr {
    fn from(value: CabernetError) -> Self {
        PyValueError::new_err(value.to_string())
    }
}
