import sounddevice as sd
import numpy as np
import time
import sys

def list_devices():
    print("\n=== Available Input Devices ===")
    devices = []
    try:
        seen_names = set()
        for i, dev in enumerate(sd.query_devices()):
            if dev['max_input_channels'] > 0:
                name = dev['name']
                # Basic filter for clearer view
                if "mapper" in name or "Sys" in name: 
                    continue
                
                print(f"ID {i}: {name}")
                devices.append(i)
    except Exception as e:
        print(f"Error listing devices: {e}")
    return devices

def test_recording(device_index):
    print(f"\n>>> Testing Device ID: {device_index}")
    
    # Try common sample rates
    rates = [44100, 16000, 48000, 8000]
    success = False
    
    for rate in rates:
        print(f"\n[Attempting Sample Rate: {rate} Hz]")
        try:
            with sd.InputStream(device=device_index, channels=1, samplerate=rate, dtype='int16') as stream:
                print(f"Stream Opened! Recording for 5 seconds...")
                print("PLEASE SPEAK INTO THE MICROPHONE NOW!")
                
                start_time = time.time()
                max_rms = 0
                
                while time.time() - start_time < 5:
                    chunk, overflow = stream.read(int(rate * 0.1)) # 100ms chunk
                    if overflow:
                        print("!", end="", flush=True)
                        
                    # Calculate RMS (Volume)
                    # Convert to float for calculation
                    data = chunk.astype(np.float32)
                    rms = np.sqrt(np.mean(data**2))
                    max_rms = max(max_rms, rms)
                    
                    # ASCII Bar
                    bar_len = int(rms / 100) 
                    bar = "#" * min(bar_len, 50)
                    print(f"\rRMS: {rms:6.1f} |{bar}", end="")
                    
                print(f"\n\nMax RMS detected: {max_rms:.1f}")
                
                if max_rms < 50:
                    print("⚠️  WARNING: Signal is very weak or silent. Check Mute switch or Privacy Settings.")
                elif max_rms > 100:
                    print("✅  SUCCESS: Audio signal detected!")
                    success = True
                    break # Stop on first success
                else:
                    print("⚠️  WEAK SIGNAL: Audio detected but very quiet.")
                    success = True
                    break
                    
        except Exception as e:
            print(f"❌ Failed at {rate} Hz: {e}")

    if not success:
        print("\n❌ Could not record audio with any standard sample rate.")
        print("Suggestions:")
        print("1. Check Windows Settings > Privacy > Microphone")
        print("2. Check if another app is using the mic exclusively.")

if __name__ == "__main__":
    print("Audio Diagnostic Tool")
    print("---------------------")
    valid_ids = list_devices()
    
    if not valid_ids:
        print("No input devices found!")
        sys.exit(1)
        
    try:
        inp = input("\nEnter Device ID to test (e.g., 1): ").strip()
        idx = int(inp)
        test_recording(idx)
    except ValueError:
        print("Invalid input. Please enter a number.")
    except KeyboardInterrupt:
        print("\nTest cancelled.")
