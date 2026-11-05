import os

def generate_fake_log():
    # Create a dummy log file in the current directory
    log_file = "service.log"
    
    print(f"Generating fake incident in {log_file}...")
    
    with open(log_file, "w") as f:
        f.write("2026-11-04 10:00:01 [INFO] PaymentService started successfully.\n")
        f.write("2026-11-04 10:05:12 [INFO] Connection established to Postgres database.\n")
        f.write("2026-11-04 10:45:33 [WARN] Memory allocation spike detected. GC overhead limit approaching.\n")
        f.write("2026-11-04 10:48:15 [ERROR] Failed to process transaction TXN-99482.\n")
        f.write("2026-11-04 10:50:00 [FATAL] java.lang.OutOfMemoryError: Java heap space\n")
        f.write("2026-11-04 10:50:01 [FATAL] PaymentService process terminated unexpectedly.\n")
        
    print(f"Incident generated! Absolute path: {os.path.abspath(log_file)}")

if __name__ == "__main__":
    generate_fake_log()
