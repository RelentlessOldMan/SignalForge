"""Run the shared test vectors in ``vectors/cases``. Format described in vectors/README.md.

Usage: ``python -m signalforge.conformance [VECTORS_DIR] [--report FILE]``. Exit 0 when every case
passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import cmath
import dataclasses
import itertools
import json
import math
import sys
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from . import (
    channel,
    dsp,
    files,
    link,
    measurements,
    metrics,
    modulation,
    spectral,
    sync,
    units,
    waveforms,
)
from .core import Signal

DEFAULT_TOL = {"abs": 1e-12, "rel": 1e-12}

OPS: dict[str, Callable[..., Any]] = {
    "lin_to_db": units.lin_to_db,
    "db_to_lin": units.db_to_lin,
    "amp_to_db": units.amp_to_db,
    "db_to_amp": units.db_to_amp,
    "hz_to_mel": units.hz_to_mel,
    "mel_to_hz": units.mel_to_hz,
    "hz_to_erb_rate": units.hz_to_erb_rate,
    "erb_rate_to_hz": units.erb_rate_to_hz,
    "erb_bandwidth": units.erb_bandwidth,
    "erb_space": units.erb_space,
    "hz_to_bark": units.hz_to_bark,
    "bark_to_hz": units.bark_to_hz,
    "a_weighting": units.a_weighting,
    "c_weighting": units.c_weighting,
    "octave_bands": units.octave_bands,
    "w_to_dbm": units.w_to_dbm,
    "dbm_to_w": units.dbm_to_w,
    "vrms_to_dbm": units.vrms_to_dbm,
    "dbm_to_vrms": units.dbm_to_vrms,
    "tone": waveforms.tone,
    "prbs": waveforms.prbs,
    "multitone": waveforms.multitone,
    "newman_phases": waveforms.newman_phases,
    "chirp": waveforms.chirp,
    "pulse_train": waveforms.pulse_train,
    "adsr": waveforms.adsr,
    "sawtooth": waveforms.sawtooth,
    "square": waveforms.square,
    "triangle": waveforms.triangle,
    "fm_tone": waveforms.fm_tone,
    "bandlimited_sawtooth": waveforms.bandlimited_sawtooth,
    "wavetable": waveforms.wavetable,
    "bandlimited_square": waveforms.bandlimited_square,
    "bandlimited_triangle": waveforms.bandlimited_triangle,
    "polyblep_sawtooth": waveforms.polyblep_sawtooth,
    "polyblep_pwm": waveforms.polyblep_pwm,
    "polyblep_square": waveforms.polyblep_square,
    "feedback_fm": waveforms.feedback_fm,
    "blit": waveforms.blit,
    "phase_distortion": waveforms.phase_distortion,
    "dpw_sawtooth": waveforms.dpw_sawtooth,
    "supersaw": waveforms.supersaw,
    "hard_sync_sawtooth": waveforms.hard_sync_sawtooth,
    "polyblep_triangle": waveforms.polyblep_triangle,
    "pwm": waveforms.pwm,
    "power_stats": measurements.power_stats,
    "autocorrelation_pitch": measurements.autocorrelation_pitch,
    "cepstrum_pitch": measurements.cepstrum_pitch,
    "temporal_centroid": measurements.temporal_centroid,
    "hjorth_parameters": measurements.hjorth_parameters,
    "permutation_entropy": measurements.permutation_entropy,
    "sample_entropy": measurements.sample_entropy,
    "gleason_index": measurements.gleason_index,
    "margalef_index": measurements.margalef_index,
    "menhinick_index": measurements.menhinick_index,
    "mcintosh_evenness": measurements.mcintosh_evenness,
    "mcintosh_dominance": measurements.mcintosh_dominance,
    "sheldon_evenness": measurements.sheldon_evenness,
    "alatalo_evenness": measurements.alatalo_evenness,
    "hill_ratio_evenness": measurements.hill_ratio_evenness,
    "bulla_evenness": measurements.bulla_evenness,
    "smith_wilson_evenness": measurements.smith_wilson_evenness,
    "camargo_evenness": measurements.camargo_evenness,
    "simpson_evenness": measurements.simpson_evenness,
    "heip_evenness": measurements.heip_evenness,
    "berger_parker_index": measurements.berger_parker_index,
    "simpson_diversity": measurements.simpson_diversity,
    "pielou_evenness": measurements.pielou_evenness,
    "hannah_kay_index": measurements.hannah_kay_index,
    "kwoka_dominance_index": measurements.kwoka_dominance_index,
    "hall_tideman_index": measurements.hall_tideman_index,
    "concentration_ratio": measurements.concentration_ratio,
    "herfindahl_index": measurements.herfindahl_index,
    "wolfson_index": measurements.wolfson_index,
    "zenga_index": measurements.zenga_index,
    "bonferroni_index": measurements.bonferroni_index,
    "quintile_share_ratio": measurements.quintile_share_ratio,
    "palma_ratio": measurements.palma_ratio,
    "lorenz_curve": measurements.lorenz_curve,
    "generalized_entropy_index": measurements.generalized_entropy_index,
    "atkinson_index": measurements.atkinson_index,
    "mean_log_deviation": measurements.mean_log_deviation,
    "coefficient_of_variation": measurements.coefficient_of_variation,
    "hoover_index": measurements.hoover_index,
    "theil_index": measurements.theil_index,
    "gini_coefficient": measurements.gini_coefficient,
    "log_relative_risk": measurements.log_relative_risk,
    "cohen_h_wald_z": measurements.cohen_h_wald_z,
    "cohen_h_standard_error": measurements.cohen_h_standard_error,
    "cohen_h": measurements.cohen_h,
    "relative_risk_reduction": measurements.relative_risk_reduction,
    "number_needed_to_treat": measurements.number_needed_to_treat,
    "risk_difference_wald_z": measurements.risk_difference_wald_z,
    "risk_difference_standard_error": measurements.risk_difference_standard_error,
    "risk_difference": measurements.risk_difference,
    "log_relative_risk_wald_z": measurements.log_relative_risk_wald_z,
    "log_relative_risk_standard_error": measurements.log_relative_risk_standard_error,
    "log_odds_ratio_wald_z": measurements.log_odds_ratio_wald_z,
    "haldane_log_odds_ratio_standard_error": measurements.haldane_log_odds_ratio_standard_error,
    "yule_y_standard_error": measurements.yule_y_standard_error,
    "yule_q_standard_error": measurements.yule_q_standard_error,
    "haldane_log_odds_ratio": measurements.haldane_log_odds_ratio,
    "log_odds_ratio_standard_error": measurements.log_odds_ratio_standard_error,
    "tetrachoric_approximation": measurements.tetrachoric_approximation,
    "symmetric_extremal_dependence_index": measurements.symmetric_extremal_dependence_index,
    "extremal_dependence_index": measurements.extremal_dependence_index,
    "extreme_dependency_score": measurements.extreme_dependency_score,
    "frequency_bias": measurements.frequency_bias,
    "prevalence_threshold": measurements.prevalence_threshold,
    "population_attributable_fraction": measurements.population_attributable_fraction,
    "attributable_fraction": measurements.attributable_fraction,
    "relative_risk": measurements.relative_risk,
    "negative_likelihood_ratio": measurements.negative_likelihood_ratio,
    "positive_likelihood_ratio": measurements.positive_likelihood_ratio,
    "binary_g_statistic": measurements.binary_g_statistic,
    "log_odds_ratio": measurements.log_odds_ratio,
    "mcnemar_statistic": measurements.mcnemar_statistic,
    "binary_chi_square": measurements.binary_chi_square,
    "chord_distance": measurements.chord_distance,
    "lance_williams_distance": measurements.lance_williams_distance,
    "variance_dissimilarity": measurements.variance_dissimilarity,
    "pattern_difference": measurements.pattern_difference,
    "shape_difference": measurements.shape_difference,
    "size_difference": measurements.size_difference,
    "dispersion_coefficient": measurements.dispersion_coefficient,
    "johnson_coefficient": measurements.johnson_coefficient,
    "gower_coefficient": measurements.gower_coefficient,
    "baroni_urbani_buser_ii": measurements.baroni_urbani_buser_ii,
    "rogot_goldberg_coefficient": measurements.rogot_goldberg_coefficient,
    "doolittle_coefficient": measurements.doolittle_coefficient,
    "benini_coefficient": measurements.benini_coefficient,
    "binary_mutual_information": measurements.binary_mutual_information,
    "gilbert_wells_coefficient": measurements.gilbert_wells_coefficient,
    "kulczynski_i": measurements.kulczynski_i,
    "sokal_sneath_iii": measurements.sokal_sneath_iii,
    "sokal_sneath_v": measurements.sokal_sneath_v,
    "sokal_sneath_iv": measurements.sokal_sneath_iv,
    "maxwell_pilliner_coefficient": measurements.maxwell_pilliner_coefficient,
    "consonni_todeschini_coefficient": measurements.consonni_todeschini_coefficient,
    "faith_coefficient": measurements.faith_coefficient,
    "gower_legendre_coefficient": measurements.gower_legendre_coefficient,
    "hawkins_dotson_coefficient": measurements.hawkins_dotson_coefficient,
    "tarwid_coefficient": measurements.tarwid_coefficient,
    "mountford_coefficient": measurements.mountford_coefficient,
    "stiles_coefficient": measurements.stiles_coefficient,
    "eyraud_coefficient": measurements.eyraud_coefficient,
    "fossum_coefficient": measurements.fossum_coefficient,
    "austin_colwell_coefficient": measurements.austin_colwell_coefficient,
    "goodman_kruskal_lambda": measurements.goodman_kruskal_lambda,
    "anderberg_d": measurements.anderberg_d,
    "cole_coefficient": measurements.cole_coefficient,
    "digby_h": measurements.digby_h,
    "pearson_heron_ii": measurements.pearson_heron_ii,
    "michael_coefficient": measurements.michael_coefficient,
    "loevinger_h": measurements.loevinger_h,
    "braun_blanquet_coefficient": measurements.braun_blanquet_coefficient,
    "gilbert_skill_score": measurements.gilbert_skill_score,
    "fager_mcgowan_coefficient": measurements.fager_mcgowan_coefficient,
    "dennis_coefficient": measurements.dennis_coefficient,
    "mcconnaughey_coefficient": measurements.mcconnaughey_coefficient,
    "forbes_coefficient": measurements.forbes_coefficient,
    "sorgenfrei_coefficient": measurements.sorgenfrei_coefficient,
    "baroni_urbani_buser_coefficient": measurements.baroni_urbani_buser_coefficient,
    "hamann_coefficient": measurements.hamann_coefficient,
    "yule_y": measurements.yule_y,
    "yule_q": measurements.yule_q,
    "ochiai_coefficient": measurements.ochiai_coefficient,
    "kulczynski_coefficient": measurements.kulczynski_coefficient,
    "sokal_sneath_coefficient": measurements.sokal_sneath_coefficient,
    "russell_rao_coefficient": measurements.russell_rao_coefficient,
    "rogers_tanimoto_coefficient": measurements.rogers_tanimoto_coefficient,
    "simple_matching_coefficient": measurements.simple_matching_coefficient,
    "tversky_index": measurements.tversky_index,
    "overlap_coefficient": measurements.overlap_coefficient,
    "hamming_distance": measurements.hamming_distance,
    "chebyshev_distance": measurements.chebyshev_distance,
    "minkowski_distance": measurements.minkowski_distance,
    "bray_curtis": measurements.bray_curtis,
    "canberra_distance": measurements.canberra_distance,
    "triangular_discrimination": measurements.triangular_discrimination,
    "cross_entropy": measurements.cross_entropy,
    "jeffreys_divergence": measurements.jeffreys_divergence,
    "renyi_divergence": measurements.renyi_divergence,
    "chi_square_divergence": measurements.chi_square_divergence,
    "total_variation_distance": measurements.total_variation_distance,
    "bhattacharyya_distance": measurements.bhattacharyya_distance,
    "hellinger_distance": measurements.hellinger_distance,
    "js_divergence": measurements.js_divergence,
    "kl_divergence": measurements.kl_divergence,
    "hodges_lehmann": measurements.hodges_lehmann,
    "cramer_von_mises": measurements.cramer_von_mises,
    "energy_distance": measurements.energy_distance,
    "wasserstein_distance": measurements.wasserstein_distance,
    "kolmogorov_smirnov": measurements.kolmogorov_smirnov,
    "vargha_delaney_a": measurements.vargha_delaney_a,
    "cliff_delta": measurements.cliff_delta,
    "glass_delta": measurements.glass_delta,
    "hedges_g": measurements.hedges_g,
    "cohen_d": measurements.cohen_d,
    "balanced_accuracy": measurements.balanced_accuracy,
    "markedness": measurements.markedness,
    "average_precision": measurements.average_precision,
    "roc_auc": measurements.roc_auc,
    "log_loss": measurements.log_loss,
    "brier_score": measurements.brier_score,
    "diagnostic_odds_ratio": measurements.diagnostic_odds_ratio,
    "fowlkes_mallows_index": measurements.fowlkes_mallows_index,
    "jaccard_index": measurements.jaccard_index,
    "youden_j": measurements.youden_j,
    "f1_score": measurements.f1_score,
    "matthews_correlation": measurements.matthews_correlation,
    "scott_pi": measurements.scott_pi,
    "cohen_kappa": measurements.cohen_kappa,
    "fleiss_kappa": measurements.fleiss_kappa,
    "icc_consistency": measurements.icc_consistency,
    "cronbach_alpha": measurements.cronbach_alpha,
    "kendall_w": measurements.kendall_w,
    "somers_d": measurements.somers_d,
    "goodman_kruskal_gamma": measurements.goodman_kruskal_gamma,
    "chatterjee_xi": measurements.chatterjee_xi,
    "blomqvist_beta": measurements.blomqvist_beta,
    "hoeffding_d": measurements.hoeffding_d,
    "biweight_midcorrelation": measurements.biweight_midcorrelation,
    "distance_correlation": measurements.distance_correlation,
    "pearson_correlation": measurements.pearson_correlation,
    "kendall_tau": measurements.kendall_tau,
    "spearman_correlation": measurements.spearman_correlation,
    "snht": measurements.snht,
    "buishand_range": measurements.buishand_range,
    "pettitt": measurements.pettitt,
    "sens_slope": measurements.sens_slope,
    "mann_kendall": measurements.mann_kendall,
    "bartels_rank_test": measurements.bartels_rank_test,
    "von_neumann_ratio": measurements.von_neumann_ratio,
    "runs_test": measurements.runs_test,
    "turning_points": measurements.turning_points,
    "ljung_box": measurements.ljung_box,
    "cosine_similarity_entropy": measurements.cosine_similarity_entropy,
    "time_irreversibility": measurements.time_irreversibility,
    "tsallis_entropy": measurements.tsallis_entropy,
    "aggregated_variance": measurements.aggregated_variance,
    "largest_lyapunov": measurements.largest_lyapunov,
    "renyi_entropy": measurements.renyi_entropy,
    "auto_mutual_information": measurements.auto_mutual_information,
    "fisher_information": measurements.fisher_information,
    "recurrence_quantification": measurements.recurrence_quantification,
    "correlation_sum": measurements.correlation_sum,
    "distribution_entropy": measurements.distribution_entropy,
    "slope_entropy": measurements.slope_entropy,
    "attention_entropy": measurements.attention_entropy,
    "bubble_entropy": measurements.bubble_entropy,
    "increment_entropy": measurements.increment_entropy,
    "weighted_permutation_entropy": measurements.weighted_permutation_entropy,
    "svd_entropy": measurements.svd_entropy,
    "dispersion_entropy": measurements.dispersion_entropy,
    "rescaled_range": measurements.rescaled_range,
    "fuzzy_entropy": measurements.fuzzy_entropy,
    "multiscale_entropy": measurements.multiscale_entropy,
    "mtie": measurements.mtie,
    "lempel_ziv_complexity": measurements.lempel_ziv_complexity,
    "katz_dimension": measurements.katz_dimension,
    "petrosian_dimension": measurements.petrosian_dimension,
    "approximate_entropy": measurements.approximate_entropy,
    "detrended_fluctuation": measurements.detrended_fluctuation,
    "time_deviation": measurements.time_deviation,
    "higuchi_dimension": measurements.higuchi_dimension,
    "hadamard_deviation": measurements.hadamard_deviation,
    "modified_allan_deviation": measurements.modified_allan_deviation,
    "allan_deviation": measurements.allan_deviation,
    "time_weighting": measurements.time_weighting,
    "octave_band_levels": measurements.octave_band_levels,
    "exceedance_levels": measurements.exceedance_levels,
    "block_leq": measurements.block_leq,
    "sound_exposure": measurements.sound_exposure,
    "schroeder_decay": measurements.schroeder_decay,
    "energy_time_curve": measurements.energy_time_curve,
    "teager_energy": measurements.teager_energy,
    "energy_separation": measurements.energy_separation,
    "gcc_phat": measurements.gcc_phat,
    "reverberation_time": measurements.reverberation_time,
    "clarity": measurements.clarity,
    "definition": measurements.definition,
    "centre_time": measurements.centre_time,
    "iacc": measurements.iacc,
    "lateral_fraction": measurements.lateral_fraction,
    "modulation_transfer": measurements.modulation_transfer,
    "speech_transmission_index": measurements.speech_transmission_index,
    "sound_strength": measurements.sound_strength,
    "stage_support": measurements.stage_support,
    "bass_ratio": measurements.bass_ratio,
    "treble_ratio": measurements.treble_ratio,
    "early_decay_time": measurements.early_decay_time,
    "decay_curvature": measurements.decay_curvature,
    "noise_compensated_decay": measurements.noise_compensated_decay,
    "decay_time": measurements.decay_time,
    "zero_crossing_rate": measurements.zero_crossing_rate,
    "power_ccdf": measurements.power_ccdf,
    "kay_frequency": measurements.kay_frequency,
    "power_ccdf_level": measurements.power_ccdf_level,
    "tone_metrics": measurements.tone_metrics,
    "sfdr": measurements.sfdr,
    "two_tone_imd": measurements.two_tone_imd,
    "two_tone_ip2": measurements.two_tone_ip2,
    "two_tone_ip5": measurements.two_tone_ip5,
    "phase_noise_ssb": measurements.phase_noise_ssb,
    "integrated_phase_noise": measurements.integrated_phase_noise,
    "phase_noise_spurs": measurements.phase_noise_spurs,
    "noise_figure_y_factor": measurements.noise_figure_y_factor,
    "noise_figure_cascade": measurements.noise_figure_cascade,
    "gain_compression": measurements.gain_compression,
    "am_am_pm": measurements.am_am_pm,
    "qpsk_map": modulation.qpsk_map,
    "qpsk_demap_hard": modulation.qpsk_demap_hard,
    "qpsk_demap_llr": modulation.qpsk_demap_llr,
    "psk8_map": modulation.psk8_map,
    "psk8_demap_hard": modulation.psk8_demap_hard,
    "psk8_demap_llr": modulation.psk8_demap_llr,
    "qam16_map": modulation.qam16_map,
    "qam16_demap_hard": modulation.qam16_demap_hard,
    "qam16_demap_llr": modulation.qam16_demap_llr,
    "qam64_map": modulation.qam64_map,
    "qam64_demap_hard": modulation.qam64_demap_hard,
    "qam64_demap_llr": modulation.qam64_demap_llr,
    "fsk_modulate": modulation.fsk_modulate,
    "ofdm_modulate": modulation.ofdm_modulate,
    "ofdm_demodulate": modulation.ofdm_demodulate,
    "fsk_demod_noncoherent": modulation.fsk_demod_noncoherent,
    "bit_errors": metrics.bit_errors,
    "fft": spectral.fft,
    "ifft": spectral.ifft,
    "fft_frequencies": spectral.fft_frequencies,
    "window": spectral.window,
    "window_stats": spectral.window_stats,
    "welch_psd": spectral.welch_psd,
    "coherence": spectral.coherence,
    "coherence_confidence_interval": spectral.coherence_confidence_interval,
    "welch_dof": spectral.welch_dof,
    "yule_walker_psd": spectral.yule_walker_psd,
    "burg_psd": spectral.burg_psd,
    "ar_psd": spectral.ar_psd,
    "goertzel": spectral.goertzel,
    "sliding_dft": spectral.sliding_dft,
    "psd_confidence_interval": spectral.psd_confidence_interval,
    "coherence_threshold": spectral.coherence_threshold,
    "coherent_output_power": spectral.coherent_output_power,
    "cross_spectral_density": spectral.cross_spectral_density,
    "transfer_function": spectral.transfer_function,
    "transfer_function_h2": spectral.transfer_function_h2,
    "dpss_tapers": spectral.dpss_tapers,
    "harmonic_f_test": spectral.harmonic_f_test,
    "generalized_lomb_scargle": spectral.generalized_lomb_scargle,
    "lomb_scargle_multiterm": spectral.lomb_scargle_multiterm,
    "multitaper_line_removal": spectral.multitaper_line_removal,
    "multitaper_psd": spectral.multitaper_psd,
    "spectrogram": spectral.spectrogram,
    "lomb_scargle": spectral.lomb_scargle,
    "lomb_scargle_false_alarm": spectral.lomb_scargle_false_alarm,
    "lomb_scargle_false_alarm_baluev": spectral.lomb_scargle_false_alarm_baluev,
    "lomb_scargle_false_alarm_level": spectral.lomb_scargle_false_alarm_level,
    "lomb_scargle_bootstrap": spectral.lomb_scargle_bootstrap,
    "lomb_scargle_false_alarm_level_baluev": spectral.lomb_scargle_false_alarm_level_baluev,
    "lomb_scargle_frequencies": spectral.lomb_scargle_frequencies,
    "occupied_bandwidth": spectral.occupied_bandwidth,
    "channel_power": spectral.channel_power,
    "acpr": spectral.acpr,
    "noise_power_ratio": spectral.noise_power_ratio,
    "spectral_flatness": spectral.spectral_flatness,
    "spectral_flux": spectral.spectral_flux,
    "spectral_irregularity": spectral.spectral_irregularity,
    "spectral_peaks": spectral.spectral_peaks,
    "interpolate_peak": spectral.interpolate_peak,
    "find_tones": spectral.find_tones,
    "peak_widths": spectral.peak_widths,
    "harmonic_series": spectral.harmonic_series,
    "inharmonicity": spectral.inharmonicity,
    "odd_even_ratio": spectral.odd_even_ratio,
    "tristimulus": spectral.tristimulus,
    "harmonic_deviation": spectral.harmonic_deviation,
    "harmonic_centroid": spectral.harmonic_centroid,
    "real_cepstrum": spectral.real_cepstrum,
    "minimum_phase": spectral.minimum_phase,
    "mel_filterbank": spectral.mel_filterbank,
    "dct": spectral.dct,
    "idct": spectral.idct,
    "mfcc": spectral.mfcc,
    "delta": spectral.delta,
    "cepstral_lifter": spectral.cepstral_lifter,
    "analytic_signal": spectral.analytic_signal,
    "frequency_shift": spectral.frequency_shift,
    "instantaneous_frequency": spectral.instantaneous_frequency,
    "spectral_variation": spectral.spectral_variation,
    "band_energy_ratio": spectral.band_energy_ratio,
    "harmonic_to_noise": spectral.harmonic_to_noise,
    "spectral_contrast": spectral.spectral_contrast,
    "spectral_crest": spectral.spectral_crest,
    "spectral_decrease": spectral.spectral_decrease,
    "spectral_entropy": spectral.spectral_entropy,
    "db_bandwidth": spectral.db_bandwidth,
    "spectral_moments": spectral.spectral_moments,
    "spectral_shape": spectral.spectral_shape,
    "spectral_slope": spectral.spectral_slope,
    "spectral_rolloff": spectral.spectral_rolloff,
    "acpr_rrc": spectral.acpr_rrc,
    "convolve": dsp.convolve,
    "autocorrelation": dsp.autocorrelation,
    "cross_correlation": dsp.cross_correlation,
    "levinson": dsp.levinson,
    "burg": dsp.burg,
    "ar_order_selection": dsp.ar_order_selection,
    "lpc_cepstrum": dsp.lpc_cepstrum,
    "line_spectral_frequencies": dsp.line_spectral_frequencies,
    "lsf_to_lpc": dsp.lsf_to_lpc,
    "lattice_filter": dsp.lattice_filter,
    "lattice_synthesis": dsp.lattice_synthesis,
    "ar_spectral_flatness": dsp.ar_spectral_flatness,
    "reflection_to_autocorrelation": dsp.reflection_to_autocorrelation,
    "reflection_to_lar": dsp.reflection_to_lar,
    "lar_to_reflection": dsp.lar_to_reflection,
    "reflection_to_arcsine": dsp.reflection_to_arcsine,
    "arcsine_to_reflection": dsp.arcsine_to_reflection,
    "itakura_saito": dsp.itakura_saito,
    "cepstral_distance": dsp.cepstral_distance,
    "bandwidth_expansion": dsp.bandwidth_expansion,
    "lpc_to_autocorrelation": dsp.lpc_to_autocorrelation,
    "schur": dsp.schur,
    "cepstrum_to_lpc": dsp.cepstrum_to_lpc,
    "lagrange_fir": dsp.lagrange_fir,
    "reflection_to_lpc": dsp.reflection_to_lpc,
    "lpc_to_reflection": dsp.lpc_to_reflection,
    "upsample": dsp.upsample,
    "rrc_taps": dsp.rrc_taps,
    "pulse_shape": dsp.pulse_shape,
    "fir_lowpass": dsp.fir_lowpass,
    "fir_highpass": dsp.fir_highpass,
    "fir_bandpass": dsp.fir_bandpass,
    "fir_equiripple": dsp.fir_equiripple,
    "kaiser_parameters": dsp.kaiser_parameters,
    "fir_group_delay": dsp.fir_group_delay,
    "fir_least_squares": dsp.fir_least_squares,
    "gammatone": dsp.gammatone,
    "fir_frequency_sampling": dsp.fir_frequency_sampling,
    "fir_response": dsp.fir_response,
    "resample": dsp.resample,
    "resample_taps": dsp.resample_taps,
    "interpolate": dsp.interpolate,
    "decimate": dsp.decimate,
    "cic_taps": dsp.cic_taps,
    "cic_compensator": dsp.cic_compensator,
    "cic_decimate": dsp.cic_decimate,
    "savgol_coefficients": dsp.savgol_coefficients,
    "savgol_filter": dsp.savgol_filter,
    "median_filter": dsp.median_filter,
    "hampel_filter": dsp.hampel_filter,
    "dc_blocker": dsp.dc_blocker,
    "comb_filter": dsp.comb_filter,
    "envelope_follower": dsp.envelope_follower,
    "moving_rms": dsp.moving_rms,
    "allpass_comb": dsp.allpass_comb,
    "moving_average": dsp.moving_average,
    "slew_limiter": dsp.slew_limiter,
    "peak_hold": dsp.peak_hold,
    "schmitt_trigger": dsp.schmitt_trigger,
    "sample_and_hold": dsp.sample_and_hold,
    "dead_zone": dsp.dead_zone,
    "quantize": dsp.quantize,
    "mu_law_compress": dsp.mu_law_compress,
    "mu_law_expand": dsp.mu_law_expand,
    "a_law_compress": dsp.a_law_compress,
    "a_law_expand": dsp.a_law_expand,
    "soft_clip": dsp.soft_clip,
    "hard_clip": dsp.hard_clip,
    "wavefold": dsp.wavefold,
    "sine_fold": dsp.sine_fold,
    "chebyshev_shaper": dsp.chebyshev_shaper,
    "rectify": dsp.rectify,
    "saturate": dsp.saturate,
    "normalize_peak": dsp.normalize_peak,
    "stereo_width": dsp.stereo_width,
    "bitcrush": dsp.bitcrush,
    "pan": dsp.pan,
    "auto_pan": dsp.auto_pan,
    "mid_side_encode": dsp.mid_side_encode,
    "mid_side_decode": dsp.mid_side_decode,
    "ring_modulate": dsp.ring_modulate,
    "tremolo": dsp.tremolo,
    "vibrato": dsp.vibrato,
    "flanger": dsp.flanger,
    "chorus": dsp.chorus,
    "phaser": dsp.phaser,
    "ping_pong_delay": dsp.ping_pong_delay,
    "haas": dsp.haas,
    "balance": dsp.balance,
    "duck": dsp.duck,
    "svf": dsp.svf,
    "auto_wah": dsp.auto_wah,
    "de_esser": dsp.de_esser,
    "two_band_compress": dsp.two_band_compress,
    "exciter": dsp.exciter,
    "octave_up": dsp.octave_up,
    "bass_enhancer": dsp.bass_enhancer,
    "octave_down": dsp.octave_down,
    "rotary": dsp.rotary,
    "vocoder": dsp.vocoder,
    "slicer": dsp.slicer,
    "schroeder_reverb": dsp.schroeder_reverb,
    "tape_stop": dsp.tape_stop,
    "lowpass_feedback_comb": dsp.lowpass_feedback_comb,
    "reverse_delay": dsp.reverse_delay,
    "stutter": dsp.stutter,
    "multitap_delay": dsp.multitap_delay,
    "pitch_shift": dsp.pitch_shift,
    "karplus_strong": dsp.karplus_strong,
    "transient_shaper": dsp.transient_shaper,
    "fade": dsp.fade,
    "crossfade": dsp.crossfade,
    "compressor_gain": dsp.compressor_gain,
    "noise_gate": dsp.noise_gate,
    "limit": dsp.limit,
    "expander_gain": dsp.expander_gain,
    "compress": dsp.compress,
    "expand": dsp.expand,
    "cic_interpolate": dsp.cic_interpolate,
    "fir_filter": lambda taps, samples, chunks: _chunked(dsp.FirFilter(taps), samples, chunks),
    "butterworth_lowpass": dsp.butterworth_lowpass,
    "butterworth_bandpass": dsp.butterworth_bandpass,
    "butterworth_bandstop": dsp.butterworth_bandstop,
    "zero_phase_filter": dsp.zero_phase_filter,
    "butterworth_highpass": dsp.butterworth_highpass,
    "linkwitz_riley": dsp.linkwitz_riley,
    "crossover_split": dsp.crossover_split,
    "chebyshev1_lowpass": dsp.chebyshev1_lowpass,
    "chebyshev1_highpass": dsp.chebyshev1_highpass,
    "chebyshev2_lowpass": dsp.chebyshev2_lowpass,
    "chebyshev2_highpass": dsp.chebyshev2_highpass,
    "elliptic_lowpass": dsp.elliptic_lowpass,
    "bessel_lowpass": dsp.bessel_lowpass,
    "low_shelf": dsp.low_shelf,
    "high_shelf": dsp.high_shelf,
    "peaking_eq": dsp.peaking_eq,
    "tilt_eq": dsp.tilt_eq,
    "bessel_highpass": dsp.bessel_highpass,
    "bessel_bandpass": dsp.bessel_bandpass,
    "allpass_first_order": dsp.allpass_first_order,
    "allpass_second_order": dsp.allpass_second_order,
    "thiran_allpass": dsp.thiran_allpass,
    "a_weighting_sos": dsp.a_weighting_sos,
    "c_weighting_sos": dsp.c_weighting_sos,
    "bessel_bandstop": dsp.bessel_bandstop,
    "elliptic_highpass": dsp.elliptic_highpass,
    "elliptic_bandpass": dsp.elliptic_bandpass,
    "elliptic_bandstop": dsp.elliptic_bandstop,
    "chebyshev1_bandpass": dsp.chebyshev1_bandpass,
    "chebyshev1_bandstop": dsp.chebyshev1_bandstop,
    "chebyshev2_bandpass": dsp.chebyshev2_bandpass,
    "chebyshev2_bandstop": dsp.chebyshev2_bandstop,
    "sos_group_delay": dsp.sos_group_delay,
    "sos_response": dsp.sos_response,
    "iir_filter": lambda sos, samples, chunks: _chunked(dsp.IirFilter(sos), samples, chunks),
    "resampler": lambda up, down, samples, chunks, taps=None: _chunked(
        dsp.Resampler(up, down, taps), samples, chunks
    ),
    "frequency_offset": channel.frequency_offset,
    "iq_imbalance": channel.iq_imbalance,
    "iq_image_rejection_db": channel.iq_image_rejection_db,
    "dc_offset": channel.dc_offset,
    "color_noise": channel.color_noise,
    "saleh_amplifier": channel.saleh_amplifier,
    "rapp_amplifier": channel.rapp_amplifier,
    "phase_noise": channel.phase_noise,
    "multipath": channel.multipath,
    "fractional_delay": channel.fractional_delay,
    "farrow_delay": channel.farrow_delay,
    "farrow_resample": channel.farrow_resample,
    "rician_fading": channel.rician_fading,
    "clock_drift": channel.clock_drift,
    "clock_jitter": channel.clock_jitter,
    "clock_offset": channel.clock_offset,
    "gardner_timing": sync.gardner_timing,
    "pi_loop_gains": sync.pi_loop_gains,
    "qpsk_carrier_tracking": sync.qpsk_carrier_tracking,
    "psk8_carrier_tracking": sync.psk8_carrier_tracking,
    "qam16_carrier_tracking": sync.qam16_carrier_tracking,
    "qam64_carrier_tracking": sync.qam64_carrier_tracking,
    "lms_equalizer": sync.lms_equalizer,
    "dfe_equalizer": sync.dfe_equalizer,
    "cma_equalizer": sync.cma_equalizer,
    "rls_equalizer": sync.rls_equalizer,
    "dfe_least_squares": sync.dfe_least_squares,
    "evm": metrics.evm,
    "qpsk_ber_theory": metrics.qpsk_ber_theory,
    "qpsk_ber_rayleigh_theory": metrics.qpsk_ber_rayleigh_theory,
    "qam16_ber_theory": metrics.qam16_ber_theory,
    "qam16_ser_theory": metrics.qam16_ser_theory,
    "qam64_ber_theory": metrics.qam64_ber_theory,
    "qam64_ser_theory": metrics.qam64_ser_theory,
    "fsk_ber_theory": metrics.fsk_ber_theory,
    "fsk_ser_theory": metrics.fsk_ser_theory,
    "psk8_ber_theory": metrics.psk8_ber_theory,
    "psk8_ser_theory": metrics.psk8_ser_theory,
    "timing_offset": sync.timing_offset,
    "qpsk_frequency_offset": sync.qpsk_frequency_offset,
    "power_frequency_offset": sync.power_frequency_offset,
    "qpsk_phase_offset": sync.qpsk_phase_offset,
    "qpsk_block_phases": sync.qpsk_block_phases,
    "psk8_phase_offset": sync.psk8_phase_offset,
    "psk8_block_phases": sync.psk8_block_phases,
    "qpsk_link": lambda **kw: link.qpsk_link(link.QpskLinkConfig(**kw)),
    "encode_samples": lambda x, datatype: files.encode_samples(x, datatype).hex(),
    "decode_samples": lambda data, datatype: files.decode_samples(_hex(data), datatype),
    "read_sigmf": lambda file: _signal_record(files.read_sigmf(_fixture(file))),
    "read_sigmf_channels": lambda file: [
        _signal_record(s) for s in files.read_sigmf_channels(_fixture(file))
    ],
    "read_sigmf_captures": lambda file: [
        _signal_record(s) for s in files.read_sigmf_captures(_fixture(file))
    ],
    "write_wav": lambda channels, sample_rate, sample_format, info=None, cues=None: _write_wav(
        channels, sample_rate, sample_format, info, cues
    ),
    "read_wav": lambda file: _wav_record(files.read_wav(_fixture(file))),
    "read_wav_info": lambda file: [
        {"id": k, "text": v} for k, v in files.read_wav_info(_fixture(file)).items()
    ],
    "read_wav_cues": lambda file: [
        {"position": float(p), "length": float(n), "label": t}
        for p, n, t in files.read_wav_cues(_fixture(file))
    ],
    "write_npy": lambda x, shape=None: _write_npy(
        x if shape is None else np.asarray(x).reshape([int(n) for n in shape])
    ),
    "read_npy": lambda file: files.read_npy(_fixture(file)),
    "read_npy_2d": lambda file: _matrix_record(files.read_npy_2d(_fixture(file))),
    "write_npz": lambda arrays: _write_npz(arrays),
    "read_npz": lambda file: [
        {"name": k, **(_matrix_record(v) if v.ndim == 2 else {"x": v})}
        for k, v in files.read_npz(_fixture(file)).items()
    ],
}


def _write_npz(arrays: Any) -> str:
    """The bytes of a .npz archive of ``{name, x}`` records, ``{name, shape, x}`` for a 2-D member
    with ``x`` flat in C order, as hex (``[]`` decodes as an array)."""
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "case.npz"
        files.write_npz(
            path,
            {}
            if isinstance(arrays, np.ndarray)
            else {
                a["name"]: np.asarray(a["x"]).reshape([int(n) for n in a["shape"]])
                if "shape" in a
                else a["x"]
                for a in arrays
            },
        )
        return path.read_bytes().hex()


def _matrix_record(a: Any) -> dict[str, Any]:
    """A 2-D array as its shape and its values flat in C order."""
    return {"shape": [float(n) for n in a.shape], "x": a.reshape(-1)}


def _write_npy(x: Any) -> str:
    """The bytes of a .npy file written from ``x``, as hex."""
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "case.npy"
        files.write_npy(path, x)
        return path.read_bytes().hex()


def _write_wav(channels: Any, sample_rate: Any, sample_format: Any, info: Any, cues: Any) -> str:
    """The bytes of a WAV file written from rows of samples, ``{id, text}`` tag records and
    ``{position, length, label}`` cue records, as hex (``[]`` decodes as an array)."""
    sigs = [Signal(np.asarray(c, dtype=np.float64), sample_rate) for c in channels]
    tags = (
        None
        if info is None
        else {}
        if isinstance(info, np.ndarray)
        else {t["id"]: t["text"] for t in info}
    )
    marks = (
        None
        if cues is None
        else []
        if isinstance(cues, np.ndarray)
        else [(_whole(c["position"]), _whole(c["length"]), c["label"]) for c in cues]
    )
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "case.wav"
        files.write_wav(path, sigs, sample_format, tags, marks)
        return path.read_bytes().hex()


def _wav_record(sigs: list[Any]) -> dict[str, Any]:
    return {
        "channels": np.stack([s.samples for s in sigs]),
        "sample_rate": sigs[0].sample_rate,
        "units": sigs[0].units,
    }


def _whole(x: Any) -> int:
    """A JSON number that must be a whole number, as an ``int``."""
    if float(x) != int(float(x)):
        raise ValueError(f"{x} is not a whole number")
    return int(float(x))


def _hex(data: Any) -> bytes:
    if not isinstance(data, str):
        raise BadCase("data must be a hex string")
    try:
        return bytes.fromhex(data)
    except ValueError:
        raise BadCase("data must be a hex string") from None


def _fixture(name: Any) -> Path:
    """A file in ``vectors/files``, named without a directory."""
    if not isinstance(name, str) or Path(name).name != name:
        raise BadCase("file must be a bare file name in vectors/files")
    return find_vectors_dir().parent / "files" / name


def _signal_record(s: Any) -> dict[str, Any]:
    """A :class:`Signal` as a record with its field names, for comparison."""
    return {
        "samples": s.samples,
        "sample_rate": s.sample_rate,
        "center_frequency": s.center_frequency,
        "time_origin": s.time_origin,
        "units": s.units,
        "impedance": s.impedance,
        "metadata": dict(s.metadata),
    }


def _chunked(f: dsp.FirFilter | dsp.IirFilter | dsp.Resampler, samples: Any, chunks: Any) -> Any:
    """Run ``samples`` through one streaming filter in chunks of the given lengths."""
    sizes = [int(c) for c in chunks]
    if any(c < 0 or c != float(x) for c, x in zip(sizes, chunks, strict=True)):
        raise BadCase("chunks must be non-negative whole numbers")
    if sum(sizes) != len(samples):
        raise BadCase("chunks must add up to the number of samples")
    edges = np.cumsum([0, *sizes])
    return np.concatenate([f.process(samples[i:j]) for i, j in itertools.pairwise(edges)])


class BadCase(Exception):
    """A vector case that is malformed (as opposed to one the library fails)."""


def decode(v: Any) -> Any:
    """JSON vector value to a Python value: complex objects, special floats, arrays."""
    if isinstance(v, str) and v in ("inf", "-inf", "nan"):
        return float(v)
    if isinstance(v, dict):
        if set(v) == {"re", "im"}:
            re, im = v["re"], v["im"]
            if isinstance(re, list):
                if not isinstance(im, list) or len(im) != len(re):
                    raise BadCase("re and im must be arrays of the same length")
                z = np.empty(len(re), dtype=np.complex128)  # re + 1j*im would turn inf into nan
                z.real = [float(decode(r)) for r in re]
                z.imag = [float(decode(i)) for i in im]
                return z
            return complex(decode(re), decode(im))
        return {k: decode(x) for k, x in v.items()}
    if isinstance(v, list):
        if any(_is_item(x) for x in v):  # a list of records or strings, not an array
            return [decode(x) for x in v]
        return np.asarray([decode(x) for x in v])
    return v


def _is_item(x: Any) -> bool:
    """Whether ``x`` makes the JSON array holding it a list rather than a number array."""
    if isinstance(x, str):
        return x not in ("inf", "-inf", "nan")
    if isinstance(x, dict):
        return set(x) != {"re", "im"}
    return x is None or isinstance(x, bool)


def _record(v: Any) -> dict[str, Any]:
    """A result record's fields and public properties, as C# reflection sees its record."""
    out = {f.name: getattr(v, f.name) for f in dataclasses.fields(v)}
    for k in dir(type(v)):
        if not k.startswith("_") and isinstance(getattr(type(v), k), property):
            out[k] = getattr(v, k)
    return out


def encode(v: Any) -> Any:
    """Python result to the JSON vector form (for reports)."""
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {k: encode(x) for k, x in _record(v).items()}
    if isinstance(v, dict):
        return {k: encode(x) for k, x in v.items()}
    if isinstance(v, tuple):
        return [encode(float(x)) for x in v]
    if isinstance(v, list):
        return [encode(x) for x in v]
    if isinstance(v, np.ndarray):
        if np.iscomplexobj(v):
            return {
                "re": [encode(float(x)) for x in v.real],
                "im": [encode(float(x)) for x in v.imag],
            }
        return [encode(x) if x.ndim else encode(x.item()) for x in v]
    if isinstance(v, complex | np.complexfloating):
        return {"re": encode(float(v.real)), "im": encode(float(v.imag))}
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, float) and not math.isfinite(v):
        return "nan" if math.isnan(v) else ("inf" if v > 0 else "-inf")
    return v


def _close(actual: complex | float, expected: complex | float, tol: dict[str, float]) -> bool:
    if isinstance(expected, float) and math.isnan(expected):
        return isinstance(actual, float | np.floating) and math.isnan(actual)
    if isinstance(expected, float) and math.isinf(expected):
        return bool(actual == expected)
    if isinstance(expected, complex) and not cmath.isfinite(expected):  # parts must match exactly
        a = complex(actual)
        return _close(a.real, expected.real, tol) and _close(a.imag, expected.imag, tol)
    return bool(abs(actual - expected) <= tol["abs"] + tol["rel"] * abs(expected))


def _kind(v: Any) -> str:
    """The vector type of a value: bool, real, complex, array, or other."""
    if isinstance(v, bool | np.bool_):
        return "bool"
    if isinstance(v, np.ndarray):
        return "complex array" if np.iscomplexobj(v) else "real array"
    if isinstance(v, complex | np.complexfloating):
        return "complex"
    if isinstance(v, int | float | np.integer | np.floating):
        return "real"
    return type(v).__name__


def compare(actual: Any, expected: Any, tol: dict[str, float], path: str = "") -> list[str]:
    """Differences between an actual result and a decoded expected value, as messages.

    Types must match exactly (a real array is not a complex array, a scalar is not a one-element
    array); booleans compare exactly, numbers within ``tol``.
    """
    where = path or "value"
    if dataclasses.is_dataclass(actual) and not isinstance(actual, type):
        actual = _record(actual)
    if expected is None or actual is None:
        if expected is None and actual is None:
            return []
        return [f"{where}: {actual!r} != expected {expected!r}"]
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{where}: expected a record, got {type(actual).__name__}"]
        out: list[str] = []
        for k, e in expected.items():
            p = f"{path}.{k}" if path else k
            out += compare(actual[k], e, tol, p) if k in actual else [f"{p}: missing"]
        return out
    if isinstance(expected, str):
        return [] if actual == expected else [f"{where}: {actual!r} != expected {expected!r}"]
    if isinstance(expected, list):
        if not isinstance(actual, list | tuple):
            return [f"{where}: expected a list, got {type(actual).__name__}"]
        if len(actual) != len(expected):
            return [f"{where}: length {len(actual)} != expected {len(expected)}"]
        return [
            d
            for i, (a, e) in enumerate(zip(actual, expected, strict=True))
            for d in compare(a, e, tol, f"{where}[{i}]")
        ]
    if isinstance(actual, list) and isinstance(expected, np.ndarray):
        actual = np.asarray(actual)
    if isinstance(actual, tuple):  # a tuple of numbers is a real array, as in the C# runner
        actual = np.asarray(actual, dtype=np.float64)
    if isinstance(actual, np.ndarray) and not np.iscomplexobj(actual) and actual.dtype != np.bool_:
        actual = np.asarray(actual, dtype=np.float64)  # uint8 bits and int arrays are real arrays
    ka, ke = _kind(actual), _kind(expected)
    if ka != ke:
        return [f"{where}: type {ka} does not match expected {ke}"]
    if ke == "bool":
        return (
            [] if bool(actual) == bool(expected) else [f"{where}: {actual} != expected {expected}"]
        )
    if isinstance(expected, np.ndarray):
        if actual.shape != expected.shape:
            return [f"{where}: shape {actual.shape} != expected {expected.shape}"]
        if expected.ndim > 1:  # rows of a 2-D result compare element by element, row-major
            actual, expected = actual.ravel(), expected.ravel()
        bad = [i for i in range(expected.size) if not _close(actual[i], expected[i], tol)]
        if bad:
            i = bad[0]
            return [f"{where}[{i}]: {actual[i]!r} != expected {expected[i]!r} ({len(bad)} differ)"]
        return []
    if not _close(actual, expected, tol):
        return [f"{where}: {actual!r} != expected {expected!r}"]
    return []


@dataclass
class CaseResult:
    file: str
    id: str
    passed: bool
    messages: list[str]
    actual: Any = None


def find_vectors_dir(start: Path | None = None) -> Path:
    """The repository's ``vectors/cases`` directory, searched upward from ``start``."""
    here = (start or Path(__file__)).resolve()
    for d in [here, *here.parents]:
        cand = d / "vectors" / "cases"
        if cand.is_dir():
            return cand
    raise FileNotFoundError("vectors/cases not found above " + str(here))


def iter_cases(vectors_dir: Path) -> Iterator[tuple[str, dict[str, Any]]]:
    for path in sorted(vectors_dir.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != 1:
            raise ValueError(f"{path.name}: unsupported schema {doc.get('schema')!r}")
        for case in doc["cases"]:
            yield path.name, case


def run_case(file: str, case: dict[str, Any]) -> CaseResult:
    cid = case["id"]
    op = OPS.get(case["op"])
    if op is None:
        return CaseResult(file, cid, False, [f"unknown op {case['op']!r}"])
    try:
        args = {k: decode(v) for k, v in case.get("args", {}).items()}
        expected = decode(case["expected"]) if "expected" in case else None
    except BadCase as e:
        return CaseResult(file, cid, False, [f"bad case: {e}"])
    tol = {**DEFAULT_TOL, **case.get("tol", {})}
    want_error = case.get("error")
    try:
        actual = op(**args)
    except TypeError as e:  # an unknown or missing argument: the case itself is wrong
        return CaseResult(file, cid, False, [f"bad case: {e}"])
    except ValueError as e:
        if want_error == "invalid_argument":
            return CaseResult(file, cid, True, [])
        return CaseResult(file, cid, False, [f"raised ValueError: {e}"])
    if want_error:
        return CaseResult(file, cid, False, [f"expected error {want_error!r}"], encode(actual))
    if "expected" not in case:
        return CaseResult(file, cid, False, ["bad case: no expected value or error"])
    msgs = compare(actual, expected, tol)
    return CaseResult(file, cid, not msgs, msgs, encode(actual))


def run_all(vectors_dir: Path) -> list[CaseResult]:
    return [run_case(f, c) for f, c in iter_cases(vectors_dir)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m signalforge.conformance")
    ap.add_argument("vectors", nargs="?", type=Path, help="vectors/cases directory")
    ap.add_argument("--report", type=Path, help="write a JSON report here")
    ns = ap.parse_args(argv)
    results = run_all(ns.vectors or find_vectors_dir(Path.cwd()))
    failed = [r for r in results if not r.passed]
    for r in failed:
        print(f"FAIL {r.file} {r.id}: {'; '.join(r.messages)}")
    print(f"{len(results) - len(failed)}/{len(results)} cases passed")
    if ns.report:
        ns.report.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "implementation": "python",
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "cases": [dataclasses.asdict(r) for r in results],
        }
        ns.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
