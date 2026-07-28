import numpy as np
import adi
import matplotlib.pyplot as plt
import time
from scipy.signal import savgol_filter

# 1. Observation Parameters
start = time.time()
sdr_ip = "ip:192.168.2.1"

int_time = 600            # Total integration time in seconds (10 minutes)
sample_rate = 3e6         # Sample rate / bandwidth (3.0 MHz)
h1_freq = 1420.405751766e6 # Rest frequency of 21cm Hydrogen Line (Hz)
center_freq = h1_freq     # SDR LO Center Frequency

num_sub_samp = 2048       # Samples per FFT frame
num_rows = 1000           # FFTs averaged per block
num_samps = num_sub_samp * num_rows
num_repeats = int(int_time / (num_samps / sample_rate))

# 2. SDR Hardware Configuration
sdr = adi.Pluto(sdr_ip)
sdr.sample_rate = int(sample_rate)
sdr.rx_lo = int(center_freq)
sdr.rx_rf_bandwidth = int(sample_rate)
sdr.rx_buffer_size = num_samps
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = 50.0  # Optimal gain for SAWbird LNA

print(f"Starting observation. Integration time: {int_time}s ({int_time/60:.1f} mins), Repeats: {num_repeats}")

# 3. Data Acquisition (Linear Power Scale)
freqs = np.fft.fftfreq(num_sub_samp, 1/sample_rate)
freqs = np.fft.fftshift(freqs)
freqs_mhz = (freqs + center_freq) / 1e6

avg_psd_linear = np.zeros(num_sub_samp)

for i in range(num_repeats):
    rx_samples = sdr.rx()
    
    # Reshape 1D sample buffer into 2D array and apply Blackman window
    rx_samples_2d = rx_samples.reshape((num_rows, num_sub_samp)) * np.blackman(num_sub_samp)
    
    # Compute 2D batched FFT
    fft_data = np.fft.fftshift(np.fft.fft(rx_samples_2d, axis=1), axes=1)
    psd_2d = np.abs(fft_data)**2
    
    # Accumulate linear power
    avg_psd_linear += np.mean(psd_2d, axis=0)
    
    if (i+1) % 50 == 0 or (i+1) == num_repeats:
        print(f"Progress: {i+1} / {num_repeats} completed ({((i+1)/num_repeats)*100:.1f}%)")

# Average linear power spectrum across all repeats (values around ~0.00125)
avg_psd_linear /= num_repeats

# 4. Signal Cleaning & Baseline Fitting
# Apply Savitzky-Golay filter to generate smooth "Cleaned Signal" (orange curve)
cleaned_psd = savgol_filter(avg_psd_linear, window_length=51, polyorder=3)

# Mask out expected HI line region (1420.1 to 1420.7 MHz) for background fit
signal_mask = (freqs_mhz > 1420.1) & (freqs_mhz < 1420.7)
baseline_mask = ~signal_mask

# Fit a 4th-order polynomial baseline to linear power
poly_coeffs = np.polyfit(freqs_mhz[baseline_mask], cleaned_psd[baseline_mask], 4)
baseline_curve = np.polyval(poly_coeffs, freqs_mhz)

# Subtract baseline to isolate the hydrogen line peak around zero
corrected_signal = cleaned_psd - baseline_curve

# Find peak position & calculate Doppler recession velocity
search_mask = (freqs_mhz > 1420.2) & (freqs_mhz < 1420.6)
local_peak_idx = np.argmax(corrected_signal[search_mask])
actual_peak_idx = np.where(search_mask)[0][local_peak_idx]

peak_freq_mhz = freqs_mhz[actual_peak_idx]
peak_val = corrected_signal[actual_peak_idx]

c = 299792.458  # Speed of light in km/s
recession_velocity = c * (h1_freq - peak_freq_mhz * 1e6) / h1_freq

# 5. Data Visualization (Matching Screenshot)
fig, ax_main = plt.subplots(figsize=(12, 6.5))

# --- MAIN PLOT ---
# Plot raw linear power ("Original Signal") and smoothed power ("Cleaned Signal")
ax_main.plot(freqs_mhz, avg_psd_linear, color="#80b1d3", alpha=0.7, linewidth=1.0, label="Original Signal")
ax_main.plot(freqs_mhz, cleaned_psd, color="#ff7f00", linewidth=1.8, label="Cleaned Signal")
ax_main.set_xlabel("Frequency (MHz)")
ax_main.set_ylabel("Amplitude")
ax_main.set_xlim(1419.0, 1421.8)
ax_main.legend(loc="upper right")

# --- INSET ZOOM PLOT ---
# Position: [left, bottom, width, height] relative to main figure box
ax_inset = fig.add_axes([0.48, 0.48, 0.40, 0.36])

# Plot corrected peak
inset_mask = (freqs_mhz >= 1419.0) & (freqs_mhz <= 1422.5)
ax_inset.plot(freqs_mhz[inset_mask], corrected_signal[inset_mask], color="#1f77b4", linewidth=1.5)

# Plot blue dot marker on top of detected peak
legend_text = f"Corrected Signal\nPeak at {peak_freq_mhz:.2f} MHz\nRecession Velocity: {recession_velocity:.2f} km/s"
ax_inset.plot(peak_freq_mhz, peak_val, 'bo', markersize=6, label=legend_text)

ax_inset.set_xlim(1419.0, 1422.5)
ax_inset.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
ax_inset.legend(loc="upper left", fontsize=8)

plt.show()

# 6. Observation Summary
end = time.time()
print("\n--- Observation Summary ---")
print(f"Peak Frequency Detected: {peak_freq_mhz:.6f} MHz")
print(f"Recession Velocity:     {recession_velocity:.2f} km/s")
print(f"Total Elapsed Time:     {end-start:.1f}s")