# Complete script to transmit a pure tone at 1.420 GHz and receive/analyze it simultaneously
import numpy as np
import adi
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime
import pandas as pd
from scipy.signal import find_peaks

start = time.time()
sdr = adi.Pluto("ip:192.168.2.1")

int_time = 60 # Total time of integration in seconds
sample_rate = 3e6 # Hz (bandwidth)
center_freq = 1420.405751766e6 # Hz (Rest frequency)
num_rows = int(1000) # Number of sdr.rx calls that average together
num_sub_samp = 1024 # Number of samples per sdr.rx call
num_samps = int(num_sub_samp) * num_rows # Total number of samples per repeat
num_repeats = int(int_time / (num_samps / sample_rate)) # Total repeats

# --- Configure the Transmitter ---
sdr.tx_rf_bandwidth = int(sample_rate)
sdr.tx_lo = int(center_freq) # Set Tx center frequency to 1.420 GHz
sdr.tx_hardwaregain_chan0 = -40 # Tx attenuation (-90 to 0 dB, safe test level)
sdr.tx_enabled_channels = [0]
sdr.tx_cyclic_buffer = True

# Transmit a pure tone at 0 Hz offset (exactly at 1.420 GHz)
sdr.dds_single_tone(0, 0.5, 0)
print(f"Transmitting pure tone at {center_freq / 1e9} GHz...")

# --- Configure the Receiver ---
sdr.sample_rate = int(sample_rate)
sdr.rx_lo = int(center_freq)
sdr.rx_rf_bandwidth = int(sample_rate)
sdr.rx_buffer_size = num_rows * num_sub_samp
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = 40.0 # Balanced gain to prevent hardware saturation

print(f"The number of repeats are {num_repeats}")

# Calculate frequencies of the spectrum
f = np.linspace(sample_rate / -2, sample_rate / 2, num_sub_samp)

list_of_repeats = []
for repeats in range(num_repeats):
    rx_samples = sdr.rx() 

    rx_samples_2d = rx_samples.reshape((num_rows, num_sub_samp))
    fft_data = np.fft.fftshift(np.fft.fft(rx_samples_2d, axis=1), axes=1)
    psd_2d = (np.abs(fft_data)**2).real
    
    psd_average_repeat = np.mean(psd_2d, axis=0)
    list_of_repeats.append(psd_average_repeat)

# Stop transmission after receiving is done
sdr.tx_enabled_channels = []

current_time = time.time()
readable_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
final_average_linear = np.mean(list_of_repeats, axis=0)
spectrum_of_repeats_dB = 10 * np.log10(list_of_repeats)
final_average_dB = 10 * np.log10(final_average_linear)

list_of_3d_matrices = []
for psd_dB in spectrum_of_repeats_dB:
    spectrum_data = np.vstack([
        np.array([current_time] * num_sub_samp),
        (center_freq + f) / 1e6,
        psd_dB
    ])
    list_of_3d_matrices.append(spectrum_data)

spectrum_of_repeats = np.dstack(list_of_3d_matrices)

average_spectrum_data = pd.DataFrame({ 
    'Timestamp' : [readable_time] * len(final_average_dB),
    'Frequency(MHz)' : (center_freq + f) / 1e6,
    'PSD(dB)' : final_average_dB
})

output_file_matrix = 'Data_of_observed_every_spectrum'
np.save(output_file_matrix, spectrum_of_repeats)

output_file_spectrum = 'Data_of_observed_spectrum.csv'
file_exists = os.path.isfile(output_file_spectrum)
with open(output_file_spectrum, 'a', newline='', encoding='utf-8') as csvfile:
    average_spectrum_data.to_csv(csvfile, header=not file_exists, index=False)
    
print(f"Every raw data successfully saved to {output_file_matrix}")
print()
print(f"Averaged spectrum data successfully saved to {output_file_spectrum}")
print()

# Plot frequency domain
plt.figure(0)
plt.title(f"Averaged frequency domain (Center :{center_freq / 1e6:.3f} MHz)")
plt.plot(average_spectrum_data['Frequency(MHz)'], average_spectrum_data['PSD(dB)'], label="ave")
plt.xlabel("Frequency [MHz]")
plt.ylabel("PSD [dB]") 
plt.legend()
plt.show()

# Spike frequency analysis
psd_values = average_spectrum_data['PSD(dB)'].values
freq_values_hz = average_spectrum_data['Frequency(MHz)'].values * 1e6

spikes = np.mean(psd_values) + (5.5 * np.std(psd_values))
peaks, _ = find_peaks(psd_values, height=spikes, distance=150, prominence=2.5)

observed_freq = freq_values_hz[peaks]

c = 299792458 # Speed of light in m/s
velocity_kms = c * (center_freq - observed_freq) / center_freq / 1000.0
z = (center_freq - observed_freq) / observed_freq
wavelength = c / observed_freq

spike_data = { 
    'Spike_Frequency(Hz)' : observed_freq,
    'Spike_PSD(dB)' : psd_values[peaks],
    'Status' : ['redshift' if v > 0 else 'blueshift' if v < 0 else 'No shift' for v in velocity_kms],
    'Wavelength(m)' : wavelength,
    'Recession_Velocity(km/s)' : velocity_kms
}

df_spikes = pd.DataFrame(spike_data)
output_file_data = 'Data_of_observed_hydrogen_line.csv'

if df_spikes.empty:
    print("No radio spike detected")
else: 
    print(df_spikes)
    print()
    df_spikes.insert(0, 'Timestamp', readable_time)
    file_exists = os.path.isfile(output_file_data)
    with open(output_file_data, 'a', newline='', encoding='utf-8') as csvfile:
        df_spikes.to_csv(csvfile, header=not file_exists, index=False)

    print(f"Data successfully saved to {output_file_data}")

print()
resolution = (sample_rate / num_sub_samp) / center_freq
print(f"The resolution of spectrum is {resolution}")
print()
end = time.time()
print(f"The total time is {end - start}s")