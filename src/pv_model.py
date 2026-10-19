"""Rooftop PV output per kWp from NASA POWER hourly data with pvlib (notebook 02)."""
import numpy as np
import pandas as pd
LAT, LON, ELEV_M = 21.15, 79.09, 310   # Nagpur
# ---- PV output per kWp from NASA POWER with pvlib (notebook 02; profile reused in 05) ----
import pvlib


def pv_output_per_kwp(power, tilt=20.0, azimuth=180.0, gamma=-0.0037, losses=0.14,
                      dc_ac_ratio=1.1, eta_inv=0.96, mount="close_mount_glass_glass"):
    """Hourly AC output (kW per kWp DC) of a rooftop PV system.

    Chain: solar position -> Erbs GHI decomposition (DNI, DHI) -> Hay-Davies transposition to the
    tilted plane -> SAPM cell temperature -> PVWatts DC model -> losses -> PVWatts inverter."""
    times = pd.DatetimeIndex(power.index).tz_localize("UTC") + pd.Timedelta("30min")   # mid-hour sun position
    loc = pvlib.location.Location(LAT, LON, altitude=ELEV_M)
    sp = loc.get_solarposition(times)
    ghi = power["ghi"].clip(lower=0).values
    dec = pvlib.irradiance.erbs(ghi, sp["zenith"].values, times)
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt, surface_azimuth=azimuth,
        solar_zenith=sp["apparent_zenith"].values, solar_azimuth=sp["azimuth"].values,
        dni=np.nan_to_num(dec["dni"]), ghi=ghi, dhi=np.nan_to_num(dec["dhi"]),
        dni_extra=pvlib.irradiance.get_extra_radiation(times).values, model="haydavies")
    poa_g = np.nan_to_num(np.asarray(poa["poa_global"], float))
    prm = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"][mount]
    tcell = pvlib.temperature.sapm_cell(poa_g, power["t2m"].values, power["ws10m"].values, **prm)
    pdc = pvlib.pvsystem.pvwatts_dc(poa_g, tcell, 1.0, gamma) * (1 - losses)
    pac = pvlib.inverter.pvwatts(pdc, 1.0 / dc_ac_ratio, eta_inv_nom=eta_inv)
    out = pd.DataFrame({"pv_kw_per_kwp": np.clip(np.nan_to_num(pac), 0, None),
                        "poa": poa_g, "tcell": tcell}, index=power.index)
    return out
