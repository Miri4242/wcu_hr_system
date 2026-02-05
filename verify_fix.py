
import sys
import os

# Set encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

sys.path.append('c:\\Users\\Gulnar Cebrayilova\\PycharmProjects\\HR_Sistemi')

try:
    from app import TURNSTILE_CONFIG
    
    def verify_fix():
        readers_to_check = ['10.0.0.95-2-In', '10.0.0.95-3-In', '10.0.0.95-4-In']
        
        print("Checking TURNSTILE_CONFIG...")
        
        all_in = TURNSTILE_CONFIG['IN']
        all_out = TURNSTILE_CONFIG['OUT']
        
        for reader in readers_to_check:
            status = "MISSING ❌"
            if reader in all_in:
                status = "FOUND IN 'IN' LIST ✅"
            elif reader in all_out:
                status = "FOUND IN 'OUT' LIST ✅"
            
            print(f"Reader '{reader}': {status}")

    if __name__ == "__main__":
        verify_fix()

except Exception as e:
    print(f"Error importing app: {e}")
