use crate::ue::UE;
use crate::error::Result;
pub struct Manager {
    pub ues: Vec<UE>,
}

impl Manager {
    pub fn new() -> Self {
        Manager { ues: Vec::new() }
    }

    pub fn send_frame(&self, frame: Vec<u8>) -> usize{
        0
    }

    pub fn poll_frame(&self) -> Option<Vec<u8>>{
        None
    }

    pub fn create_ue(&mut self, ip: String) -> Result<()>{
        Ok(())
    }

    pub fn change_ip(&mut self, old_ip: String, new_ip: String) -> Result<()>{
        Ok(())
    }
}
