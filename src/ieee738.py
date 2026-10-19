"""IEEE Std 738-2012 steady-state conductor rating (heat balance), implemented from scratch (notebook 03).
Validated against the standard's Drake 26/7 ACSR example (about 1025 A)."""
import numpy as np

def air_properties(T_film, elev_m):
    mu = 1.458e-6 * (T_film + 273.0) ** 1.5 / (T_film + 383.4)                              # Pa·s
    rho = (1.293 - 1.525e-4 * elev_m + 6.379e-9 * elev_m ** 2) / (1 + 0.00367 * T_film)      # kg/m³
    k = 2.424e-2 + 7.477e-5 * T_film - 4.407e-9 * T_film ** 2                                # W/(m·°C)
    return mu, rho, k

def convective_cooling(Ts, Ta, D, wind, elev_m, phi_deg=90.0):
    T_film = (Ts + Ta) / 2.0
    mu, rho, k = air_properties(T_film, elev_m)
    phi = np.radians(phi_deg)
    K_angle = 1.194 - np.cos(phi) + 0.194 * np.cos(2 * phi) + 0.368 * np.sin(2 * phi)
    N_re = D * rho * wind / mu
    qc1 = K_angle * (1.01 + 1.35 * N_re ** 0.52) * k * (Ts - Ta)
    qc2 = K_angle * 0.754 * N_re ** 0.6 * k * (Ts - Ta)
    qcn = 3.645 * rho ** 0.5 * D ** 0.75 * np.maximum(Ts - Ta, 0) ** 1.25
    return np.maximum(np.maximum(qc1, qc2), qcn)

def radiative_cooling(Ts, Ta, D, emissivity):
    return 17.8 * D * emissivity * (((Ts + 273.0) / 100) ** 4 - ((Ta + 273.0) / 100) ** 4)

def solar_heating(Q, D, absorptivity):
    return absorptivity * Q * D

def clear_sky_flux(lat_deg, day_of_year, hour, line_azimuth_deg, elev_m, atmosphere="clear"):
    # IEEE 738-2012 clear-sky solar flux on the conductor, Qse·sin(theta) in W/m²
    lat = np.radians(lat_deg)
    decl = np.radians(23.46 * np.sin(np.radians((284 + day_of_year) / 365.0 * 360.0)))
    omega = np.radians((hour - 12.0) * 15.0)
    Hc = np.arcsin(np.cos(lat) * np.cos(decl) * np.cos(omega) + np.sin(lat) * np.sin(decl))
    chi = np.sin(omega) / (np.sin(lat) * np.cos(omega) - np.cos(lat) * np.tan(decl))
    if np.degrees(omega) < 0:
        C = 0.0 if chi >= 0 else 180.0
    else:
        C = 180.0 if chi >= 0 else 360.0
    Zc = C + np.degrees(np.arctan(chi))
    coeffs = {"clear": [-42.2391, 63.8044, -1.9220, 3.46921e-2, -3.61118e-4, 1.94318e-6, -4.07608e-9],
              "industrial": [53.1821, 14.2110, 6.6138e-1, -3.1658e-2, 5.4654e-4, -4.3446e-6, 1.3236e-8]}[atmosphere]
    Hd = np.degrees(Hc)
    Qs = sum(c * Hd ** i for i, c in enumerate(coeffs))
    K_solar = 1 + 1.148e-4 * elev_m - 1.108e-8 * elev_m ** 2
    theta = np.arccos(np.cos(Hc) * np.cos(np.radians(Zc - line_azimuth_deg)))
    return K_solar * Qs * np.sin(theta), Hd, Zc

def ac_resistance(Ts, c):
    return c["R_lo"] + (c["R_hi"] - c["R_lo"]) / (c["T_hi"] - c["T_lo"]) * (Ts - c["T_lo"])

def ampacity(Ta, wind, Q_solar, c, Ts=None, elev_m=0.0, phi_deg=90.0, terms=False):
    Ts = c["Ts_max"] if Ts is None else Ts
    qc = convective_cooling(Ts, Ta, c["D"], wind, elev_m, phi_deg)
    qr = radiative_cooling(Ts, Ta, c["D"], c["emissivity"])
    qs = solar_heating(Q_solar, c["D"], c["absorptivity"])
    R = ac_resistance(Ts, c)
    I = np.sqrt(np.maximum(qc + qr - qs, 0) / R)
    return (I, dict(qc=qc, qr=qr, qs=qs, R=R)) if terms else I

DRAKE = dict(name="Drake 26/7 ACSR", D=0.02814, R_lo=7.283e-5, T_lo=25.0, R_hi=8.688e-5, T_hi=75.0,
             emissivity=0.8, absorptivity=0.8, Ts_max=100.0)

