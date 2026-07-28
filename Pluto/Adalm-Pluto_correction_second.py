import numpy as np
import adi
import matplotlib.pyplot as plt
import time
from scipy import signal

# 1. Observation Parameters
start = time.time()
sdr_ip = "ip:192.168.2.1"

int_time = 600            # Total integration time in seconds (10 minutes)
sample_rate = 3e6         # Sample rate / bandwidth (3.0 MHz)
h1_freq = 1420.405751766e6 # Rest frequency of 21cm Hydrogen Line (Hz)
center_freq = h1_freq     # SDR LO Center Frequency tuned directly to H1 line

num_sub_samp = 2048       # Samples per FFT frame
num_rows = 1000           # FFTs averaged per block
num_samps = num_sub_samp * num_rows
num_repeats = int(int_time / (num_samps / sample_rate))

# 2. Gain & Digital Bandpass Filter
def correct_gain_and_bandpass(rx_samples, sample_rate, low_cutoff=50e3, high_cutoff=1.3e6):
    """
    Normalizes signal power and removes DC offset spike & passband edge roll-offs.
    """
    # Step A: Power normalization
    power = np.mean(np.abs(rx_samples)**2)
    rx_samples_norm = rx_samples / np.sqrt(power) if power > 0 else rx_samples

    # Step B: Digital 4th-order Butterworth bandpass filter
    nyquist = sample_rate / 2.0
    sos = signal.butter(4, [low_cutoff / nyquist, high_cutoff / nyquist], 
                        btype='bandpass', output='sos')
    
    i_filtered = signal.sosfilt(sos, rx_samples_norm.real)
    q_filtered = signal.sosfilt(sos, rx_samples_norm.imag)
    
    return i_filtered + 1j * q_filtered

# 3. SDR Configuration
sdr = adi.Pluto(sdr_ip)
sdr.sample_rate = int(sample_rate)
sdr.rx_lo = int(center_freq)
sdr.rx_rf_bandwidth = int(sample_rate)
sdr.rx_buffer_size = num_samps
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = 50.0  # Optimal gain setting for SAWbird LNA

print(f"Starting observation. Integration time: {int_time}s ({int_time/60:.1f} mins), Repeats: {num_repeats}")

# 4. Data Acquisition Loop
freqs = np.fft.fftfreq(num_sub_samp, 1/sample_rate)
freqs = np.fft.fftshift(freqs)
freqs_mhz = (freqs + center_freq) / 1e6

avg_psd_linear = np.zeros(num_sub_samp)

for i in range(num_repeats):
    raw_samples = sdr.rx()
    
    # Apply Gain Normalization & Digital Filtering
    rx_samples = correct_gain_and_bandpass(raw_samples, sample_rate)
    
    # Reshape for 2D batched FFT
    rx_samples_2d = rx_samples.reshape((num_rows, num_sub_samp))
    rx_samples_2d = rx_samples_2d * np.blackman(num_sub_samp)
    
    fft_data = np.fft.fftshift(np.fft.fft(rx_samples_2d, axis=1), axes=1)
    psd_2d = np.abs(fft_data)**2
    
    avg_psd_linear += np.mean(psd_2d, axis=0)
    
    if (i+1) % 50 == 0 or (i+1) == num_repeats:
        print(f"Progress: {i+1} / {num_repeats} completed ({((i+1)/num_repeats)*100:.1f}%)")

avg_psd_linear /= num_repeats
psd_db = 10 * np.log10(avg_psd_linear + 1e-12)

# 5. Baseline Correction & Positive Ratio Conversion
# Mask out expected H1 emission region (1420.1 to 1420.7 MHz)
signal_mask = (freqs_mhz > 1420.1) & (freqs_mhz < 1420.7)
valid_band_mask = (freqs_mhz > (center_freq - 1.2e6)/1e6) & (freqs_mhz < (center_freq + 1.2e6)/1e6)
baseline_mask = (~signal_mask) & valid_band_mask

poly_coeffs = np.polyfit(freqs_mhz[baseline_mask], psd_db[baseline_mask], 4)
baseline_curve = np.polyval(poly_coeffs, freqs_mhz)

# Flatten spectrum in dB
flat_psd_db = psd_db - baseline_curve

# Convert to Linear Power Ratio (1.0 = Noise floor, >1.0 = Positive Hydrogen Line Signal)
flat_psd_linear = 10 ** (flat_psd_db / 10.0)

# 6. Visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

# Plot 1: Raw Power Spectrum (Negative dB Scale) vs Fitted Baseline
ax1.set_title("Raw Power Spectrum with Fitted Baseline Curve")
ax1.plot(freqs_mhz, psd_db, color="gray", label="Raw Spectrum (Negative dB)")
ax1.plot(freqs_mhz, baseline_curve, color="red", linestyle="--", label="Fitted Baseline Noise")
ax1.axvline(x=h1_freq/1e6, color='blue', linestyle=':', label="Rest H1 Freq (1420.406 MHz)")
ax1.set_ylabel("Power [dBFS]")
ax1.set_xlim(1419.2, 1421.6)
ax1.legend()

# Plot 2: Detected Positive Signal (Linear Power Ratio)
ax2.set_title("Detected 21cm Hydrogen Line Signal (Positive Linear Ratio)")
ax2.plot(freqs_mhz, flat_psd_linear, color="darkgreen", label="Signal Ratio (1.0 = Baseline Noise)")
ax2.axhline(y=1.0, color='gray', linestyle='--', label="Noise Floor Baseline (1.0)")
ax2.axvline(x=h1_freq/1e6, color='blue', linestyle=':', label="Rest H1 Freq (1420.406 MHz)")
ax2.set_xlabel("Frequency [MHz]")
ax2.set_ylabel("Relative Power Ratio")
ax2.set_xlim(1419.2, 1421.6)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend()

plt.tight_layout()
plt.show()

# 7. Doppler Velocity Calculation
search_mask = (freqs_mhz > 1420.2) & (freqs_mhz < 1420.6)
peak_idx = np.argmax(flat_psd_db[search_mask])
actual_peak_idx = np.where(search_mask)[0][peak_idx]

observed_freq = freqs_mhz[actual_peak_idx] * 1e6
c = 299792.458  # Speed of light in km/s

velocity_kms = c * (h1_freq - observed_freq) / h1_freq

print("\n--- Observation Summary ---")
print(f"Peak Frequency Detected: {observed_freq/1e6:.6f} MHz")
print(f"Peak Signal Ratio:      {flat_psd_linear[actual_peak_idx]:.3f}x above noise floor ({flat_psd_db[actual_peak_idx]:.2f} dB)")
print(f"Doppler Shift Velocity:  {velocity_kms:.2f} km/s")

if flat_psd_db[actual_peak_idx] > 0.3:
    print("Status: Strong 21cm Hydrogen line candidate detected!")
else:
    print("Status: Signal is weak or absent. Verify antenna pointing.")

end = time.time()
print(f"Processing complete. Elapsed time: {end-start:.1f}s")