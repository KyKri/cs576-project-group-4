use layer3::Cabernet;

fn main() {
    let mut c = Cabernet::with_internet("10.0.0.3", "10.0.0.0.0/24").unwrap();
    c.create_ue("10.0.0.4").unwrap();
    c.create_ue("10.0.0.5").unwrap();
    let mut i = 0;
    loop {
        i += 1;
        if let Some(f) = c.poll_frame() {
            println!("Got frame of size {}", f.len());
            let iph = etherparse::Ipv4HeaderSlice::from_slice(&f).unwrap();
            println!("Src IP: {}", iph.source_addr());
            println!("Dst IP: {}", iph.destination_addr());
            if let Err(e) = c.send_frame(f) {
                eprintln!("Error sending frame: {e}")
            };
        }
        if i == 5 {
            println!("deleting 10.0.0.5 after 10 frames");
            c.delete_ue("10.0.0.5").unwrap();
        }
    }
}
