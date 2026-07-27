import numpy as np
import adi
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime
import pandas as pd
from scipy.signal import find_peaks
from scipy import signal

start = time.time()
sdr = adi.Pluto("ip:192.168.2.1")

int_time = 600 #total time of integration in seconds
sample_rate = 3e6 # Hz (bandwidth)
center_freq = 1420.405751766e6 # Hz
num_rows = int(1000) #number of sdr.rx calls that average together to produce a sample spectra 
num_sub_samp = 1024 #number of samples at the sample rate that the SDR averages together and reports vis sdr.rx
num_samps = int(num_sub_samp)*num_rows # total number
num_repeats = int(int_time/(num_samps/sample_rate)) #a repeat is a full set of num_rows

# Config Rx (setting for Rxpin)
sdr.sample_rate = int(sample_rate)
sdr.rx_lo = int(center_freq) # set what center frequency you want
sdr.rx_rf_bandwidth = int(sample_rate) # filter width, just set it to the same as sample rate for now
sdr.rx_buffer_size = num_rows * num_sub_samp # how many samples you want
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = 50.0 

print(f"The number of repeats are {num_repeats}")

#calculateing the frequencies of the spect
f = np.linspace(sample_rate/-2, sample_rate/2, num_sub_samp)

list_of_repeats = []
for repeats in range(num_repeats):
    rx_samples = sdr.rx() 

    rx_samples_2d = rx_samples.reshape((num_rows, num_sub_samp))
    fft_data = np.fft.fftshift(np.fft.fft(rx_samples_2d, axis=1), axes=1)
    psd_2d = (np.abs(fft_data)**2).real
    
    psd_average_repeat = np.mean(psd_2d, axis=0)
    list_of_repeats.append(psd_average_repeat)

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

output_file_matrix='Data_of_observed_every_spectrum'
np.save(output_file_matrix, spectrum_of_repeats) #save the raw data for each repeat in 3D .npy file

output_file_spectrum = 'Data_of_observed_spectrum.csv'
file_exists = os.path.isfile(output_file_spectrum)
with open(output_file_spectrum, 'a', newline='', encoding='utf-8') as csvfile:
    average_spectrum_data.to_csv(csvfile, header=not file_exists, index=False)
    
print (f"Every raw data successfully saved to {output_file_matrix}")
print()
print(f"Averaged spectrum data successfully saved to {output_file_spectrum}")
print()

# Plot freq domain
plt.figure(0)
plt.title(f"Averaged frequency domain (Center :{center_freq/1e6:.3f} MHz)")

plt.plot(average_spectrum_data['Frequency(MHz)'], average_spectrum_data['PSD(dB)'],label="ave")
plt.xlabel("Frequency [MHz]")
plt.ylabel("PSD [dB]") 
plt.legend()
plt.show()

#Spike freq
psd_values = average_spectrum_data['PSD(dB)'].values
freq_values_hz = average_spectrum_data['Frequency(MHz)'].values * 1e6

spikes = np.mean(psd_values) + (5 * np.std(psd_values))
peaks, _ = find_peaks(psd_values, height=spikes, distance=100, prominence=2)

observed_freq = freq_values_hz[peaks]

z=(center_freq-observed_freq)/observed_freq #equation for redshift/blueshift

c=299792458 #speed of light in m

wavelength=c/observed_freq

spike_data = { 'Spike_Frequency(Hz)' : observed_freq,
               'Spike_PSD(dB)' : psd_values[peaks],
               'Status' :['redshift' if val>0 else 'blueshift' if val<0 else 'No shift' for val in z],
               'Wavelength(m)' : wavelength,
               'Rec/ession Velocity(km/s)' : z*c/1000
             }

df_spikes = pd.DataFrame(spike_data)

output_file_data = 'Data_of_observed_hydrogen_line.csv'

# Plot, analyze, and save the spike
if df_spikes.empty:
    print("No radio spike detected")

else: 
    print(df_spikes)
    print()
    print(f"z = {z}")
    print()
    df_spikes.insert(0, 'Timestamp', readable_time)
    file_exists = os.path.isfile(output_file_data)
    with open(output_file_data, 'a', newline='', encoding='utf-8') as csvfile:
        df_spikes.to_csv(csvfile, header=not file_exists, index=False)
        
    print(f"Data successfully saved to {output_file_data}")

print()
resolution=((sample_rate)/(num_sub_samp))/(center_freq)

print(f"The resolution of spectrum iws {resolution}")
print()
end = time.time()
print(f"The total time is {end-start}s")