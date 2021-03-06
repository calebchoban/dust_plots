import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
plt.switch_backend('agg')
from scipy.stats import binned_statistic_2d
from scipy.optimize import curve_fit
import pickle
import os
from readsnap import readsnap
from astropy.table import Table
import gas_temperature as gas_temp
from tasz import *
from observations import *
from analytic_dust_yields import *
import plot_setup as plt_set

from config import *


def calc_rotate_matrix(vec1, vec2):
	""""
	Gives the rotation matrix between two unit vectors
	"""
	a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
	v = np.cross(a, b)
	c = np.dot(a, b)
	s = np.linalg.norm(v)
	kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
	rotation_matrix = np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))
	return rotation_matrix



def weighted_percentile(a, percentiles=np.array([50, 16, 84]), weights=None):
	"""
	Calculates percentiles associated with a (possibly weighted) array

	Parameters
	----------
	a : array-like
	    The input array from which to calculate percents
	percentiles : array-like
	    The percentiles to calculate (0.0 - 100.0)
	weights : array-like, optional
	    The weights to assign to values of a.  Equal weighting if None
	    is specified

	Returns
	-------
	values : np.array
	    The values associated with the specified percentiles.  
	"""

	# First deal with empty array
	if len(a)==0:
		return np.full(len(percentiles), np.nan)

	# Standardize and sort based on values in a
	percentiles = percentiles
	if weights is None:
		weights = np.ones(a.size)
	idx = np.argsort(a)
	a_sort = a[idx]
	w_sort = weights[idx]

	# Get the percentiles for each data point in array
	p=1.*w_sort.cumsum()/w_sort.sum()*100
	# Get the value of a at the given percentiles
	values=np.interp(percentiles, p, a_sort)
	return values


def plot_observational_data(axis, param, elem=None, log=True, CO_opt='S12', goodSNR=True):
	"""
	Plots observational D/Z data vs the given param.

	Parameters
	----------
	axis : Matplotlib axis
		Axis on which to plot the data
	param: string
		Parameters to plot D/Z against (fH2, nH, Z, r, sigma_dust)
	log : boolean
		Plot on log scale

	Returns
	-------
	None

	"""
	if param == 'fH2':
		data = Chiang_20_DZ_vs_param(param, CO_opt=CO_opt, bin_nums=30, log=True, goodSNR=goodSNR)
		for i, gal_name in enumerate(data.keys()):
			fH2_vals = data[gal_name][0]; mean_DZ = data[gal_name][1]; std_DZ = data[gal_name][2]
			if log:
				std_DZ[std_DZ == 0] = EPSILON
			axis.errorbar(fH2_vals, mean_DZ, yerr = np.abs(mean_DZ-np.transpose(std_DZ)), label=gal_name, c=MARKER_COLORS[i], fmt=MARKER_STYLES[i], elinewidth=1, markersize=6,zorder=2)
	elif param == 'r':
		data = Chiang_20_DZ_vs_param(param, bin_data=True, CO_opt=CO_opt, phys_r=True, bin_nums=30, log=False, goodSNR=goodSNR)
		for i, gal_name in enumerate(data.keys()):
			r_vals = data[gal_name][0]; mean_DZ = data[gal_name][1]; std_DZ = data[gal_name][2]
			if log:
				std_DZ[std_DZ == 0] = EPSILON
			axis.errorbar(r_vals, mean_DZ, yerr = np.abs(mean_DZ-np.transpose(std_DZ)), label=gal_name, c=MARKER_COLORS[i], fmt=MARKER_STYLES[i], elinewidth=1, markersize=6,zorder=2)
	elif param == 'r25':
		data = Chiang_20_DZ_vs_param('r', bin_data=True, CO_opt=CO_opt, phys_r=False, bin_nums=30, log=False, goodSNR=goodSNR)
		for i, gal_name in enumerate(data.keys()):
			r_vals = data[gal_name][0]; mean_DZ = data[gal_name][1]; std_DZ = data[gal_name][2]
			if log:
				std_DZ[std_DZ == 0] = EPSILON
			axis.errorbar(r_vals, mean_DZ, yerr = np.abs(mean_DZ-np.transpose(std_DZ)), label=gal_name, c=MARKER_COLORS[i], fmt=MARKER_STYLES[i], elinewidth=1, markersize=6,zorder=2)
	elif param == 'nH':
		dens_vals, DZ_vals = Jenkins_2009_DZ_vs_dens(phys_dens=True)
		axis.plot(dens_vals, DZ_vals, label='Jenkins09 w/ Phys. Dens.', c='xkcd:black', linestyle=LINE_STYLES[0], linewidth=LINE_WIDTHS[5], zorder=2)
		dens_vals, DZ_vals = Jenkins_2009_DZ_vs_dens(phys_dens=False)
		axis.plot(dens_vals, DZ_vals, label='Jenkins09', c='xkcd:black', linestyle=LINE_STYLES[1], linewidth=LINE_WIDTHS[5], zorder=2)
	elif param == 'sigma_dust':
		data = Chiang_20_DZ_vs_param(param, bin_data=True, CO_opt=CO_opt, bin_nums=30, log=True, goodSNR=goodSNR)
		for i, gal_name in enumerate(data.keys()):
			sigma_vals = data[gal_name][0]; mean_DZ = data[gal_name][1]; std_DZ = data[gal_name][2]
			if log:
				std_DZ[std_DZ == 0] = EPSILON
			axis.errorbar(sigma_vals, mean_DZ, yerr = np.abs(mean_DZ-np.transpose(std_DZ)), label=gal_name, c=MARKER_COLORS[i], fmt=MARKER_STYLES[i], elinewidth=1, markersize=6,zorder=2)	
	elif param == 'sigma_gas':
		data = Chiang_20_DZ_vs_param(param, bin_data=True, CO_opt=CO_opt, bin_nums=30, log=True, goodSNR=True)
		for i, gal_name in enumerate(data.keys()):
			sigma_vals = data[gal_name][0]; mean_DZ = data[gal_name][1]; std_DZ = data[gal_name][2]
			if log:
				std_DZ[std_DZ == 0] = EPSILON
			axis.errorbar(sigma_vals, mean_DZ, yerr = np.abs(mean_DZ-np.transpose(std_DZ)), label=gal_name, c=MARKER_COLORS[i], fmt=MARKER_STYLES[i], elinewidth=1, markersize=6,zorder=2)	
		if not goodSNR:
			data = Chiang_20_DZ_vs_param(param, bin_data=False, CO_opt=CO_opt, log=True, goodSNR=False)
			for i, gal_name in enumerate(data.keys()):
				sigma_vals = data[gal_name][0]; DZ = data[gal_name][1]
				axis.scatter(sigma_vals, DZ, c=MARKER_COLORS[i], marker=MARKER_STYLES[i], s=2, zorder=0, alpha=0.4)	
	elif param == 'sigma_H2':
		data = Chiang_20_DZ_vs_param(param, bin_data=True, CO_opt=CO_opt, bin_nums=30, log=True, goodSNR=goodSNR)
		for i, gal_name in enumerate(data.keys()):
			sigma_vals = data[gal_name][0]; mean_DZ = data[gal_name][1]; std_DZ = data[gal_name][2]
			if log:
				std_DZ[std_DZ == 0] = EPSILON
			axis.errorbar(sigma_vals, mean_DZ, yerr = np.abs(mean_DZ-np.transpose(std_DZ)), label=gal_name, c=MARKER_COLORS[i], fmt=MARKER_STYLES[i], elinewidth=1, markersize=6,zorder=2)	
	elif param == 'depletion':
		dens_vals, DZ_vals = Jenkins_2009_DZ_vs_dens(elem=elem, phys_dens=False)
		axis.plot(dens_vals, 1.-DZ_vals, label='Jenkins09', c='xkcd:black', linestyle=LINE_STYLES[1], linewidth=LINE_WIDTHS[5], zorder=2)
		dens_vals, DZ_vals = Jenkins_2009_DZ_vs_dens(elem=elem, phys_dens=True)
		axis.plot(dens_vals, 1.-DZ_vals, label='Jenkins09 w/ Phys. Dens.', c='xkcd:black', linestyle=LINE_STYLES[0], linewidth=LINE_WIDTHS[5], zorder=2)
	elif param == 'sigma_Z':
		# TO DO: Add Remy-Ruyer D/Z vs Z observed data
		print("D/Z vs Z observations have not been implemented yet")
	else:
		print("D/Z vs %s observational data is not available."%param)



def DZ_vs_params(params, param_lims, gas, header, center_list, r_max_list, Lz_list=None, height_list=None, bin_nums=50, time=False, depletion=False, \
	          cosmological=True, labels=None, foutname='DZ_vs_param.png', std_bars=True, style='color', log=True, include_obs=True, CO_opt='S12', Rd=None):
	"""
	Plots the average dust-to-metals ratio (D/Z) vs given parameters given code values of center and virial radius for multiple simulations/snapshots

	Parameters
	----------
	param: array
		Array of parameters to plot D/Z against (fH2, nH, Z, r, r25)
	param_lims: array
		Limits for each parameter given in params
	gas : array
	    Array of snapshot gas data structures
	header : array
		Array of snapshot header structures
	center_list : array
		array of 3-D coordinate of center of circles
	r_max_list : array
		array of maximum radii
	Lz_list : array
		List of Lz unit vectors if selecting particles in disk
	height_list : array
		List of disk heights if applicable
	bin_nums : int
		Number of bins to use
	time : bool
		Print time in corner of plot (useful for movies)
	depletion: bool, optional
		Was the simulation run with the DEPLETION option
	cosmological : bool
		Is the simulation cosmological
	labels : array
		Array of labels for each data set
	foutname: str, optional
		Name of file to be saved
	std_bars : bool
		Include standard deviation bars for the data
	style : string
		Plotting style when plotting multiple data sets
		'color' - gives different color and linestyles to each data set
		'size' - make all lines solid black but with varying line thickness
	log : boolean
		Plot log of D/Z
	include_obs : boolean
		Overplot observed data if available
	 Rd : array
		Array of stellar scale radii to be used in plots vs radius

	Returns
	-------
	None
	"""	

	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(gas), style=style)

	# Set up subplots based on number of parameters given
	fig,axes = plt_set.setup_figure(len(params))

	for i, x_param in enumerate(params):
		# Set up for each plot
		axis = axes[i]
		x_lim = param_lims[i]

		y_param = 'DZ'
		plt_set.setup_axis(axis, x_param, y_param, x_lim=x_lim)

		# First plot observational data if applicable
		if include_obs:
			plot_observational_data(axis, x_param, log=log, CO_opt=CO_opt, goodSNR=True)

		for j in range(len(gas)):
			G = gas[j]; H = header[j]; center = center_list[j]; r_max = r_max_list[j]; 
			if Lz_list != None:
				Lz_hat = Lz_list[j]; disk_height = height_list[j];
			else:
				Lz_hat = None; disk_height = None;

			mean_DZ,std_DZ,param_vals = calc_DZ_vs_param(x_param, x_lim, G, center, r_max, Lz_hat=Lz_hat, disk_height=disk_height, depletion=depletion)
			# Replace zeros with small values since we are taking the log of the values
			if log:
				std_DZ[std_DZ == 0] = EPSILON
				mean_DZ[mean_DZ == 0] = EPSILON
			if x_param == 'r25':
				param_vals = param_vals/(4.*Rd[j])

			# Only need to label the seperate simulations in the first plot
			if i==0:
				axis.plot(param_vals, mean_DZ, label=labels[j], linestyle=linestyles[j], color=colors[j], linewidth=linewidths[j], zorder=3)
			else:
				axis.plot(param_vals, mean_DZ, linestyle=linestyles[j], color=colors[j], linewidth=linewidths[j], zorder=3)
			if std_bars:
				axis.fill_between(param_vals, std_DZ[:,0], std_DZ[:,1], alpha = 0.3, color=colors[j], zorder=1)

		if include_obs:
			axis.legend(loc=0, fontsize=SMALL_FONT, frameon=False, ncol=2)
		else:
			axis.legend(loc=0, fontsize=SMALL_FONT, frameon=False)

	if time:
		if cosmological:
			z = H['redshift']
			axes[0].text(.05, .95, 'z = ' + '%.2g' % z, color="xkcd:black", fontsize = LARGE_FONT, ha = 'left', transform=axes[0].transAxes, zorder=4)
		else:
			t = H['time']
			axes[0].text(.05, .95, 't = ' + '%2.2g Gyr' % t, color="xkcd:black", fontsize = LARGE_FONT, ha = 'left', transform=axes[0].transAxes, zorder=4)	
	plt.tight_layout()	
	plt.savefig(foutname)
	plt.close()	


def calc_DZ_vs_param(param, param_lims, G, center, r_max, Lz_hat=None, disk_height=5, bin_nums=50, depletion=False):
	"""
	Calculate the average dust-to-metals ratio (D/Z) vs radius, density, and Z given code values of center and virial radius for multiple simulations/snapshots

	Parameters
	----------
	param: string
		Name of parameter to get D/Z values for
	G : dict
	    Snapshot gas data structure
	center : array
		3-D coordinate of center of circle
	r_max : double
		maximum radii of gas particles to use
	Lz_hat: array
		Unit vector of Lz to be used to mask only 
	disk_height: double
		Height of disk to mask if Lz_hat is given, default is 5 kpc
	bin_nums : int
		Number of bins to use
	depletion : bool, optional
		Was the simulation run with the DEPLETION option
	Returns
	-------
	mean_DZ : array
		Array of mean D/Z values vs parameter given
	std_DZ : array
		Array of 16th and 84th percentiles D/Z values
	param_vals : array
		Parameter values D/Z values are taken over
	"""	

	param_min = param_lims[0]; param_max = param_lims[1]; 

	coords = np.copy(G['p']) # Since we edit coords need to make a deep copy
	coords -= center
	# Get only data of particles in sphere/disk since those are the ones we care about
	# Also gives a nice speed-up
	# Get paticles in disk
	if Lz_hat != None:
		zmag = np.dot(coords,Lz_hat)
		r_z = np.zeros(np.shape(coords))
		r_z[:,0] = zmag*Lz_hat[0]
		r_z[:,1] = zmag*Lz_hat[1]
		r_z[:,2] = zmag*Lz_hat[2]
		r_s = np.subtract(coords,r_z)
		smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
		in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
	# Get particles in sphere otherwise
	else:
		in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

	M = G['m'][in_galaxy]*1E10
	coords = coords[in_galaxy]
	if depletion:
		DZ = (G['dz'][:,0]/(G['z'][:,0]+G['dz'][:,0]))[in_galaxy]
	else:
		DZ = (G['dz'][:,0]/G['z'][:,0])[in_galaxy]

	mean_DZ = np.zeros(bin_nums - 1)
	# 16th and 84th percentiles
	std_DZ = np.zeros([bin_nums - 1,2])

	# Get D/Z values over number density of Hydrogen (nH)
	if param == 'nH':
		if depletion:
			nH = G['rho'][in_galaxy]*UnitDensity_in_cgs * ( 1. - (G['z'][:,0][in_galaxy]+G['z'][:,1]+G['dz'][:,0][in_galaxy])) / H_MASS
		else:
			nH = G['rho'][in_galaxy]*UnitDensity_in_cgs * ( 1. - (G['z'][:,0][in_galaxy]+G['z'][:,1][in_galaxy])) / H_MASS

		# Make bins for nH 
		nH_bins = np.logspace(np.log10(param_min),np.log10(param_max),bin_nums)
		param_vals = (nH_bins[1:] + nH_bins[:-1]) / 2.
		digitized = np.digitize(nH,nH_bins)

		for j in range(1,len(nH_bins)):
			if len(nH[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				weights = M[digitized == j]
				values = DZ[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=weights)

	# Get D/Z values over gas temperature
	elif param == 'T':
		T = gas_temp.gas_temperature(G)
		T = T[in_galaxy]

		# Make bins for T
		T_bins = np.logspace(np.log10(param_min),np.log10(param_max),bin_nums)
		param_vals = (T_bins[1:] + T_bins[:-1]) / 2.
		digitized = np.digitize(T,T_bins)

		for j in range(1,len(T_bins)):
			if len(T[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				weights = M[digitized == j]
				values = DZ[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=weights)

	# Get D/Z valus over radius of galaxy from the center
	elif param == 'r' or param == 'r25':
		r_bins = np.linspace(0, r_max, num=bin_nums)
		param_vals = (r_bins[1:] + r_bins[:-1]) / 2.

		for j in range(bin_nums-1):
			# find all coordinates within shell
			r_min = r_bins[j]; r_max = r_bins[j+1];

			# If disk get particles in annulus
			if Lz_hat!=None:
				zmag = np.dot(coords,Lz_hat)
				r_z = np.zeros(np.shape(coords))
				r_z[:,0] = zmag*Lz_hat[0]
				r_z[:,1] = zmag*Lz_hat[1]
				r_z[:,2] = zmag*Lz_hat[2]
				r_s = np.subtract(coords,r_z)
				smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
				in_shell = np.where((np.abs(zmag) <= disk_height) & (smag <= r_max) & (smag > r_min))
			# Else get particles in shell
			else:
				in_shell = np.logical_and(np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.), np.sum(np.power(coords,2),axis=1) > np.power(r_min,2.))
			weights = M[in_shell]
			values = DZ[in_shell]
			if len(values) > 0:
				mean_DZ[j],std_DZ[j,0],std_DZ[j,1] = weighted_percentile(values, weights=weights)
			else:
				mean_DZ[j] = np.nan
				std_DZ[j,0] = np.nan; std_DZ[j,1] = np.nan;

	# Get D/Z values vs total metallicty of gas
	elif param == 'Z':
		solar_Z = 0.02
		if depletion:
			Z = (G['z'][:,0]+G['dz'][:,0])[in_galaxy]/solar_Z
		else:
			Z = G['z'][:,0][in_galaxy]/solar_Z

		Z_bins = np.logspace(np.log10(param_min),np.log10(param_max),bin_nums)
		param_vals = (Z_bins[1:] + Z_bins[:-1]) / 2.
		digitized = np.digitize(Z,Z_bins)

		for j in range(1,len(Z_bins)):
			if len(Z[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				weights = M[digitized == j]
				values = DZ[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=weights)
	# Get D/Z values vs H2 mass fraction of gas
	elif param == 'fH2':
		NH1,NHion,NH2 = calc_H_fracs(G)
		fH2 = 2*NH2[in_galaxy]/(NH1[in_galaxy]+2*NH2[in_galaxy])
		fH2_bins = np.logspace(np.log10(param_min),np.log10(param_max),bin_nums)
		param_vals = (fH2_bins[1:] + fH2_bins[:-1]) / 2.
		digitized = np.digitize(fH2,fH2_bins)

		if depletion:
			nH = G['rho'][in_galaxy]*UnitDensity_in_cgs * ( 1. - (G['z'][:,0][in_galaxy]+G['z'][:,1]+G['dz'][:,0][in_galaxy])) / H_MASS
		else:
			nH = G['rho'][in_galaxy]*UnitDensity_in_cgs * ( 1. - (G['z'][:,0][in_galaxy]+G['z'][:,1][in_galaxy])) / H_MASS


		for j in range(1,len(fH2_bins)):
			if len(fH2[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				weights = M[digitized == j]
				values = DZ[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=weights)
	else:
		print("Parameter given to calc_DZ_vs_param is not supported:",param)
		return None,None,None

	return mean_DZ, std_DZ, param_vals


def observed_DZ_vs_param(params, param_lims, gas, header, center_list, r_max_list, Lz_list=None, \
			height_list=None, bin_nums=50, time=False, depletion=False, cosmological=True, labels=None, \
			foutname='obs_DZ_vs_param.png', std_bars=True, style='color', log=True, include_obs=True, CO_opt='S12'):
	"""
	Plots mock observations of dust-to-metals vs various parameters for multiple simulations 

	Parameters
	----------
	gas : array
	    Array of snapshot gas data structures
	header : array
		Array of snapshot header structures
	center_list : array
		array of 3-D coordinate of center of circles
	r_max_list : array
		array of maximum radii
	bin_nums : int
		Number of bins to use
	time : bool
		Print time in corner of plot (useful for movies)
	depletion: bool, optional
		Was the simulation run with the DEPLETION option
	cosmological : bool
		Is the simulation cosmological
	labels : array
		Array of labels for each data set
	foutname: str, optional
		Name of file to be saved
	std_bars : bool
		Include standard deviation bars for the data
	style : string
		Plotting style when plotting multiple data sets
		'color' - gives different color and linestyles to each data set
		'size' - make all lines solid black but with varying line thickness
	log : boolean
		Plot log of D/Z
	include_obs : boolean
		Overplot observed data if available

	Returns
	-------
	None
	"""	

	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(gas), style=style)

	# Set up subplots based on number of parameters given
	fig,axes = plt_set.setup_figure(len(params))

	for i, x_param in enumerate(params):
		# Set up for each plot
		axis = axes[i]
		x_lim = param_lims[i]
		y_param = 'DZ'
		plt_set.setup_axis(axis, x_param, y_param, x_lim=x_lim)

		# First plot observational data if applicable
		if include_obs:
			plot_observational_data(axis, x_param, log=log, CO_opt=CO_opt, goodSNR=False)

		for j in range(len(gas)):
			G = gas[j]; H = header[j]; center = center_list[j]; r_max = r_max_list[j]; 
			if Lz_list != None:
				Lz_hat = Lz_list[j]; disk_height = height_list[j];
			else:
				Lz_hat = None; disk_height = None;

			mean_DZ,std_DZ,param_vals = calc_obs_DZ_vs_param(x_param, x_lim, G, center, r_max, Lz_hat=Lz_hat, disk_height=disk_height, depletion=depletion)
			# Replace zeros with small values since we are taking the log of the values
			if log:
				std_DZ[std_DZ == 0] = EPSILON
				mean_DZ[mean_DZ == 0] = EPSILON

			# Only need to label the seperate simulations in the first plot
			if i==0:
				axis.plot(param_vals, mean_DZ, label=labels[j], linestyle=linestyles[j], color=colors[j], linewidth=linewidths[j], zorder=3)
			else:
				axis.plot(param_vals, mean_DZ, linestyle=linestyles[j], color=colors[j], linewidth=linewidths[j], zorder=3)
			if std_bars:
				axis.fill_between(param_vals, std_DZ[:,0], std_DZ[:,1], alpha = 0.3, color=colors[j], zorder=1)

		if include_obs:
			axis.legend(loc=0, fontsize=SMALL_FONT, frameon=False, ncol=2)
		else:
			axis.legend(loc=0, fontsize=SMALL_FONT, frameon=False)	

	if time:
		if cosmological:
			z = H['redshift']
			axes[0].text(.05, .95, 'z = ' + '%.2g' % z, color="xkcd:black", fontsize = LARGE_FONT, ha = 'left', transform=axes[0].transAxes ,zorder=4)
		else:
			t = H['time']
			axes[0].text(.05, .95, 't = ' + '%2.2g Gyr' % t, color="xkcd:black", fontsize = LARGE_FONT, ha = 'left', transform=axes[0].transAxes, zorder=4)	
	plt.tight_layout()	
	plt.savefig(foutname)
	plt.close()	


def calc_obs_DZ_vs_param(param, param_lims, G, center, r_max, Lz_hat=None, disk_height=5, param_bins=50, pixel_res = 2, depletion=False):
	"""
	Calculate the average dust-to-metals ratio vs radius, gas , H2 , metal, or dust surface density
	given code values of center and viewing direction for multiple simulations/snapshots

	Parameters
	----------
	param: string
		Name of parameter to get D/Z values for
	G : dict
	    Snapshot gas data structure
	center : array
		3-D coordinate of center of circle
	r_max : double
		maximum radii of gas particles to use
	Lz_hat: array
		Unit vector of Lz to be used to mask only 
	disk_height: double
		Height of disk to mask if Lz_hat is given, default is 5 kpc
	param_bins : int
		Number of bins to use for physical param
	pixel_res : double
		Size resolution of each pixel bin in kpc
	depletion : bool, optional
		Was the simulation run with the DEPLETION option
	Returns
	-------
	mean_surf_dens : array
		Array of mean dust surface density values vs parameter given
	std_surf_dens : array
		Array of 16th and 84th percentiles dust surface density values
	param_vals : array
		Parameter values dust surface density values are taken over
	"""	

	param_min = param_lims[0]; param_max = param_lims[1]; 

	coords = np.copy(G['p']) # Since we edit coords need to make a deep copy
	coords -= center
	# Get only data of particles in sphere/disk since those are the ones we care about
	# Also gives a nice speed-up
	# Get paticles in disk
	if Lz_hat != None:
		zmag = np.dot(coords,Lz_hat)
		r_z = np.zeros(np.shape(coords))
		r_z[:,0] = zmag*Lz_hat[0]
		r_z[:,1] = zmag*Lz_hat[1]
		r_z[:,2] = zmag*Lz_hat[2]
		r_s = np.subtract(coords,r_z)
		smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
		in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
	# Get particles in sphere otherwise
	else:
		in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

	NH1,NHion,NH2=calc_H_fracs(G)
	NH1=NH1[in_galaxy];NHion=NHion[in_galaxy];NH2=NH2[in_galaxy];
	M = G['m'][in_galaxy]*1E10
	coords = coords[in_galaxy]
	dust_mass = G['dz'][in_galaxy,0]*M
	if depletion:
		Z_mass = G['z'][in_galaxy,0] * M + dust_mass
	else:
		Z_mass = G['z'][in_galaxy,0] * M

	x = coords[:,0];y=coords[:,1];
	pixel_bins = int(np.ceil(2*r_max/pixel_res))
	x_bins = np.linspace(-r_max,r_max,pixel_bins)
	y_bins = np.linspace(-r_max,r_max,pixel_bins)
	x_vals = (x_bins[1:] + x_bins[:-1]) / 2.
	y_vals = (y_bins[1:] + y_bins[:-1]) / 2.
	pixel_area = pixel_res**2 * 1E6 # area of pixel in pc^2
	
	mean_DZ = np.zeros(param_bins - 1)
	std_DZ = np.zeros([param_bins - 1,2])


	if param == 'sigma_dust':
		ret = binned_statistic_2d(x, y, [Z_mass,dust_mass], statistic=np.sum, bins=[x_bins,y_bins]).statistic
		DZ_pixel = ret[1].flatten()/ret[0].flatten()
		dust_pixel = ret[1].flatten()/pixel_area

		# Now bin the data 
		dust_bins = np.logspace(np.log10(param_min),np.log10(param_max),param_bins)
		param_vals = (dust_bins[1:] + dust_bins[:-1]) / 2.
		digitized = np.digitize(dust_pixel,dust_bins)

		for j in range(1,len(dust_bins)):
			if len(dust_pixel[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				values = DZ_pixel[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=None)

	elif param=='sigma_gas':
		ret = binned_statistic_2d(x, y, [Z_mass,dust_mass,M], statistic=np.sum, bins=[x_bins,y_bins]).statistic
		DZ_pixel = ret[1].flatten()/ret[0].flatten()
		M_pixel = ret[2].flatten()/pixel_area

		# Now bin the data 
		gas_bins = np.logspace(np.log10(param_min),np.log10(param_max),param_bins)
		param_vals = (gas_bins[1:] + gas_bins[:-1]) / 2.
		digitized = np.digitize(M_pixel,gas_bins)

		for j in range(1,len(gas_bins)):
			if len(M_pixel[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				values = DZ_pixel[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=None)

	elif param=='sigma_H2':
		MH2=2*NH2*H_MASS*Grams_to_Msolar
		ret = binned_statistic_2d(x, y, [Z_mass,dust_mass,MH2], statistic=np.sum, bins=[x_bins,y_bins]).statistic
		DZ_pixel = ret[1].flatten()/ret[0].flatten()
		MH2_pixel = ret[2].flatten()/pixel_area

		# Now bin the data 
		gas_bins = np.logspace(np.log10(param_min),np.log10(param_max),param_bins)
		param_vals = (gas_bins[1:] + gas_bins[:-1]) / 2.
		digitized = np.digitize(MH2_pixel,gas_bins)

		for j in range(1,len(gas_bins)):
			if len(MH2_pixel[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				values = DZ_pixel[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=None)

	elif param == 'r':
		mean_DZ = np.zeros(pixel_bins/2 - 1)
		std_DZ = np.zeros([pixel_bins/2 - 1,2])
		ret = binned_statistic_2d(x, y, [Z_mass,dust_mass], statistic=np.sum, bins=[x_bins,y_bins],expand_binnumbers=True)
		DZ_pixel = ret.statistic[1].flatten()/ret.statistic[0].flatten()
		# Get the average r coordinate for each pixel in kpc
		pixel_r_vals = np.array([np.sqrt(np.power(np.abs(y_vals),2) + np.power(np.abs(x_vals[k]),2)) for k in range(len(x_vals))]).flatten()

		r_bins = np.linspace(0, r_max, num=pixel_bins/2)
		param_vals = (r_bins[1:] + r_bins[:-1]) / 2.

		for j in range(pixel_bins/2-1):
			# find all coordinates within shell
			r_min = r_bins[j]; r_max = r_bins[j+1];
			in_shell = np.where((pixel_r_vals <= r_max) & (pixel_r_vals > r_min))
			values = DZ_pixel[in_shell]
			if len(values) > 0:
				mean_DZ[j],std_DZ[j,0],std_DZ[j,1] = weighted_percentile(values, weights=None)
			else:
				mean_DZ[j] = np.nan
				std_DZ[j,0] = np.nan; std_DZ[j,1] = np.nan;

	elif param == 'fH2':
		MH1=NH1*H_MASS*Grams_to_Msolar
		MH2=2*NH2*H_MASS*Grams_to_Msolar
		ret = binned_statistic_2d(x, y, [Z_mass,dust_mass,MH2,MH1], statistic=np.sum, bins=[x_bins,y_bins]).statistic
		DZ_pixel = ret[1].flatten()/ret[0].flatten()
		fH2_pixel = ret[2].flatten()/(ret[2].flatten()+ret[3].flatten())

		# Now bin the data 
		fH2_bins = np.linspace(param_min,param_max,param_bins)
		param_vals = (fH2_bins[1:] + fH2_bins[:-1]) / 2.
		digitized = np.digitize(fH2_pixel,fH2_bins)

		for j in range(1,len(fH2_bins)):
			if len(fH2_pixel[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				values = DZ_pixel[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=None)

	elif param == 'sigma_Z':
		ret = binned_statistic_2d(x, y, [Z_mass,dust_mass], statistic=np.sum, bins=[x_bins,y_bins]).statistic
		DZ_pixel = ret[1].flatten()/ret[0].flatten()
		Z_pixel = ret[0].flatten()/pixel_area

		# Now bin the data 
		Z_bins = np.logspace(np.log10(param_min),np.log10(param_max),param_bins)
		param_vals = (Z_bins[1:] + Z_bins[:-1]) / 2.
		digitized = np.digitize(Z_pixel,Z_bins)

		for j in range(1,len(Z_bins)):
			if len(Z_pixel[digitized==j])==0:
				mean_DZ[j-1] = np.nan
				std_DZ[j-1,0] = np.nan; std_DZ[j-1,1] = np.nan;
				continue
			else:
				values = DZ_pixel[digitized == j]
				mean_DZ[j-1],std_DZ[j-1,0],std_DZ[j-1,1] = weighted_percentile(values, weights=None)
	else:
		print("Parameter given to calc_dust_dens_vs_param is not supported:",param)
		return None,None,None

	return mean_DZ, std_DZ, param_vals



def calc_H_fracs(G):
	# Analytic calculation of molecular hydrogen from Krumholz et al. (2018)


	Z = G['z'][:,0] #metal mass (everything not H, He)
	# dust mean mass per H nucleus
	mu_H = 2.3E-24# grams
	# standard effective number of particle kernel neighbors defined in parameters file
	N_ngb = 32.
	# Gas softening length
	hsml = G['h']*UnitLength_in_cm
	density = G['rho']*UnitDensity_in_cgs

	sobColDens = np.multiply(hsml,density) / np.power(N_ngb,1./3.) # Cheesy approximation of column density

	#  dust optical depth 
	tau = np.multiply(sobColDens,Z*1E-21/SOLAR_Z)/mu_H
	tau[tau==0]=EPSILON #avoid divide by 0

	chi = 3.1 * (1+3.1*np.power(Z/SOLAR_Z,0.365)) / 4.1 # Approximation

	s = np.divide( np.log(1+0.6*chi+0.01*np.power(chi,2)) , (0.6 *tau) )
	s[s==-4.] = -4.+EPSILON # Avoid divide by zero
	fH2 = np.divide((1 - 0.5*s) , (1+0.25*s)) # Fraction of Molecular Hydrogen from Krumholz & Knedin
	fH2[fH2<0] = 0 #Nonphysical negative molecular fractions set to 0

	fHe = G['z'][:,1]
	fMetals = G['z'][:,0]

	# Gives number of H1, H2, and Hion atoms
	NH1   =  G['m'] * UnitMass_in_g * (1. - fHe - fMetals) * (1. - fH2) / H_MASS
	NH2   =  G['m'] * UnitMass_in_g * (1. - fHe - fMetals) * fH2 / (2*H_MASS)
	NHion =  G['m'] * UnitMass_in_g * (1. - fHe - fMetals) * (1.-G['nh']) / H_MASS
	
	return NH1,NHion,NH2



def DZ_var_in_pixel(gas, header, center_list, r_max_list, Lz_list=None, \
			height_list=None, pixel_res=2, time=False, depletion=False, cosmological=True, labels=None, \
			foutname='DZ_variation_per_pixel.png', style='color', log=True):
	"""
	Plots variation of dust-to-metals in each observed pixels for multiple simulations 

	Parameters
	----------
	gas : array
	    Array of snapshot gas data structures
	header : array
		Array of snapshot header structures
	center_list : array
		array of 3-D coordinate of center of circles
	r_max_list : array
		array of maximum radii
	pixel_res : double
		Size of pixels in kpc
	time : bool
		Print time in corner of plot (useful for movies)
	depletion: bool, optional
		Was the simulation run with the DEPLETION option
	cosmological : bool
		Is the simulation cosmological
	labels : array
		Array of labels for each data set
	foutname: str, optional
		Name of file to be saved
	style : string
		Plotting style when plotting multiple data sets
		'color' - gives different color and linestyles to each data set
		'size' - make all lines solid black but with varying line thickness
	log : boolean
		Plot log of D/Z

	Returns
	-------
	None
	"""	

	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(gas), style=style)

	fig = plt.figure() 
	axis = plt.gca()
	ylabel = r'D/Z Ratio'
	xlabel = r'Pixel Num'
	plt_set.setup_labels(axis,xlabel,ylabel)
	if log:
		axis.set_yscale('log')
		axis.set_ylim([0.01,1.0])
	else:
		axis.set_ylim([0.,1.0])


	for j in range(len(gas)):
		G = gas[j]; H = header[j]; center = center_list[j]; r_max = r_max_list[j]; 
		if Lz_list != None:
			Lz_hat = Lz_list[j]; disk_height = height_list[j];
		else:
			Lz_hat = None; disk_height = None;

		coords = np.copy(G['p']) # Since we edit coords need to make a deep copy
		coords -= center
		# Get only data of particles in sphere/disk since those are the ones we care about
		# Also gives a nice speed-up
		# Get paticles in disk
		if Lz_hat != None:
			zmag = np.dot(coords,Lz_hat)
			r_z = np.zeros(np.shape(coords))
			r_z[:,0] = zmag*Lz_hat[0]
			r_z[:,1] = zmag*Lz_hat[1]
			r_z[:,2] = zmag*Lz_hat[2]
			r_s = np.subtract(coords,r_z)
			smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
			in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
		# Get particles in sphere otherwise
		else:
			in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

		M = G['m'][in_galaxy]
		coords = coords[in_galaxy]
		dust_mass = G['dz'][in_galaxy,0]*M
		if depletion:
			Z_mass = G['z'][in_galaxy,0] * M + dust_mass
		else:
			Z_mass = G['z'][in_galaxy,0] * M

		x = coords[:,0];y=coords[:,1];
		pixel_bins = int(np.ceil(2*r_max/pixel_res))+1
		x_bins = np.linspace(-r_max,r_max,pixel_bins)
		y_bins = np.linspace(-r_max,r_max,pixel_bins)
		x_vals = (x_bins[1:] + x_bins[:-1]) / 2.
		y_vals = (y_bins[1:] + y_bins[:-1]) / 2.
		pixel_area = pixel_res**2 * 1E6 # area of pixel in pc^2

		ret = binned_statistic_2d(x, y, [Z_mass,dust_mass], statistic=np.sum, bins=[x_bins,y_bins], expand_binnumbers=True)
		data = ret.statistic
		DZ_pixel = data[1].flatten()/data[0].flatten()
		binning = ret.binnumber
		pixel_num = np.arange(len(DZ_pixel.flatten()))
		mean_DZ = np.zeros(len(pixel_num))
		std_DZ = np.zeros([len(pixel_num),2])
		for y in range(len(y_vals)):
			for x in range(len(x_vals)):
				binx = binning[0]; biny = binning[1]
				in_pixel = np.logical_and(binx == x+1, biny == y+1)
				values = dust_mass[in_pixel]/Z_mass[in_pixel]
				weights = M[in_pixel]
				mean_DZ[y*len(x_vals)+x],std_DZ[y*len(x_vals)+x,0],std_DZ[y*len(x_vals)+x,1] = weighted_percentile(values, weights=weights)

		# Now set pixel indices so we start at the center pixel and spiral outward
		N = np.sqrt(np.shape(pixel_num)[0])
		startx = N/2; starty = startx
		dirs = [(0, -1), (-1, 0), (0, 1), (1, 0)]
		x, y = startx, starty
		size = N * N
		k, indices = 0, []
		while len(indices) < size:
			for l in xrange((k % 2) * 2, (k % 2) * 2 + 2):
				dx, dy = dirs[l]
				for _ in xrange(k + 1):
					if 0 <= x < N and 0 <= y < N:
						indices += [int(y*N+x)]
					x, y = x + dx, y + dy
			k+=1

		axis.errorbar(pixel_num, mean_DZ[indices], yerr = np.abs(mean_DZ[indices]-np.transpose(std_DZ[indices])), c=colors[j], fmt=MARKER_STYLE[0], elinewidth=1, markersize=2)
		axis.plot(pixel_num, DZ_pixel[indices], label=labels[j], linestyle=linestyles[j], color=colors[j], linewidth=linewidths[j])
		

	axis.legend(loc=0, fontsize=SMALL_FONT, frameon=False)
	plt.savefig(foutname)
	plt.close()	



def elem_depletion_vs_param(elems, param, param_lim, gas, header, center_list, r_max_list, Lz_list=None, \
			height_list=None, bin_nums=50, time=False, depletion=False, cosmological=True, labels=None, \
			foutname='obs_elem_dep_vs_dens.png', std_bars=True, style='color', log=True, include_obs=True):
	"""
	Plots mock observations of specified elemental depletion vs various parameters for multiple simulations 

	Parameters
	----------
	elems : array
		Array of which elements you want to plot depletions for
	param : string
		Name of parameter to get depletion values for
	param_lim : array
		Limits for plotting parameter
	gas : array
	    Array of snapshot gas data structures
	header : array
		Array of snapshot header structures
	center_list : array
		array of 3-D coordinate of center of circles
	r_max_list : array
		array of maximum radii
	bin_nums : int
		Number of bins to use
	time : bool
		Print time in corner of plot (useful for movies)
	depletion: bool, optional
		Was the simulation run with the DEPLETION option
	cosmological : bool
		Is the simulation cosmological
	labels : array
		Array of labels for each data set
	phys_dens : boolean
		Use physical 3D densities or mean sight-line densities
	foutname: str, optional
		Name of file to be saved
	std_bars : bool
		Include standard deviation bars for the data
	style : string
		Plotting style when plotting multiple data sets
		'color' - gives different color and linestyles to each data set
		'size' - make all lines solid black but with varying line thickness
	log : boolean
		Plot log of depletion
	include_obs : boolean
		Overplot observed data if available

	Returns
	-------
	None
	"""	

	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(gas), style=style)

	# Set up subplots based on number of parameters given
	fig,axes = plt_set.setup_figure(len(elems))

	for i,elem in enumerate(elems):
		axis = axes[i]
		elem_indx = ELEMENTS.index(elem)
		plt_set.setup_axis(axis, param, 'depletion', x_lim=param_lim)

		if include_obs and param == 'nH':
			plot_observational_data(axis, param='depletion', elem=elem, log=log)

		for j in range(len(gas)):
			G = gas[j]; H = header[j]; center = center_list[j]; r_max = r_max_list[j];
			if Lz_list != None:
				Lz_hat = Lz_list[j]; disk_height = height_list[j];
			else:
				Lz_hat = None; disk_height = None;

			coords = np.copy(G['p']) # Since we edit coords need to make a deep copy
			coords -= center
			# Get only data of particles in sphere/disk since those are the ones we care about
			# Also gives a nice speed-up
			# Get paticles in disk
			if Lz_hat != None:
				zmag = np.dot(coords,Lz_hat)
				r_z = np.zeros(np.shape(coords))
				r_z[:,0] = zmag*Lz_hat[0]
				r_z[:,1] = zmag*Lz_hat[1]
				r_z[:,2] = zmag*Lz_hat[2]
				r_s = np.subtract(coords,r_z)
				smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
				in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
			# Get particles in sphere otherwise
			else:
				in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

			coords = coords[in_galaxy]
			M = G['m'][in_galaxy]

			if param == 'nH':
				param_data = G['rho'][in_galaxy]*UnitDensity_in_cgs * ( 1. - (G['z'][:,0][in_galaxy]+G['z'][:,1][in_galaxy])) / H_MASS
				param_bins = np.logspace(np.log10(param_lim[0]),np.log10(param_lim[1]),bin_nums)
				param_vals = (param_bins[1:] + param_bins[:-1]) / 2.

			elif param == 'fH2':
				NH1,NHion,NH2 = calc_H_fracs(G)
				param_data = 2*NH2[in_galaxy]/(NH1[in_galaxy]+2*NH2[in_galaxy])
				param_bins = np.linspace(param_lim[0],param_lim[1],bin_nums)
				param_vals = (param_bins[1:] + param_bins[:-1]) / 2.


			mean_DZ = np.zeros(bin_nums-1)
			std_DZ = np.zeros([bin_nums-1,2])
		
			if depletion:
				DZ = (G['dz'][:,elem_indx]/(G['z'][:,elem_indx]+G['dz'][:,elem_indx]))[in_galaxy]
			else:
				DZ = (G['dz'][:,elem_indx]/G['z'][:,elem_indx])[in_galaxy]

			# Deal with DZ>1 values
			DZ[DZ>1] = 1.

			digitized = np.digitize(param_data,param_bins)


			for k in range(1,len(param_bins)):
				if len(param_data[digitized==k])==0:
					mean_DZ[k-1] = np.nan
					std_DZ[k-1,0] = np.nan; std_DZ[k-1,1] = np.nan;
					continue
				else:
					weights = M[digitized == k]
					values = DZ[digitized == k]
					mean_DZ[k-1],std_DZ[k-1,0],std_DZ[k-1,1] = weighted_percentile(values, weights=weights)
			axis.plot(param_vals, 1.-mean_DZ, label=labels[j], linestyle=linestyles[j], color=colors[j], linewidth=linewidths[j], zorder=3)
			if std_bars:
				axis.fill_between(param_vals, 1.-std_DZ[:,0], 1.-std_DZ[:,1], alpha = 0.3, color=colors[j], zorder=1)

		# Only need legend on first plot
		if i == 0:
			if include_obs:
				axis.legend(loc=0, fontsize=SMALL_FONT, frameon=False, ncol=2)
			else:
				axis.legend(loc=0, fontsize=SMALL_FONT, frameon=False)

		axis.text(.10, .40, elem, color="xkcd:black", fontsize = 2*LARGE_FONT, ha = 'center', va = 'center', transform=axis.transAxes)

	plt.tight_layout()
	plt.savefig(foutname)



"""
def inst_dust_prod(gas, header, center_list, r_max_list,  Lz_list=None, height_list=None, bin_nums=100, time=False, depletion=False, log = False, \
	           cosmological=True, Tmin=1, Tmax=1E5, Tcut=300, labels=None, foutname='inst_dust_prod.png', style='color', implementation='species', \
	           t_ref_factors = None):

	Make plot of instantaneous dust growth for a given snapshot depending on the dust evolution implementation used

	Parameters
	----------
	gas : array
	    Array of snapshot gas data structure
	header : array
		Array of snapshot header structure
	bin_nums: int
		Number of bins to use
	time : bool, optional
		Print time in corner of plot (useful for movies)
	style : string
		Plotting style when plotting multiple data sets
		'color' - gives different color and linestyles to each data set
		'size' - make all lines solid black but with varying line thickness

	Returns
	-------
	None


	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(gas), style=style)

	fig,axes = plt.subplots(1, 1, figsize=(12,10))

	for i in range(len(gas)):
		if t_ref_factors != None:
			t_ref_factor = t_ref_factors[i]
		else:
			t_ref_factor = 1.

		if isinstance(implementation, list):
			imp = implementation[i]
		else:
			imp = implementation

		G = gas[i]; H = header[i]; center = center_list[i]; r_max = r_max_list[i];
		if Lz_list != None:
			Lz_hat = Lz_list[i]; disk_height = height_list[i];
		else:
			Lz_hat = None; disk_height = None;

		coords = np.copy(G['p']) # Since we edit coords need to make a deep copy
		coords -= center
		# Get only data of particles in sphere/disk since those are the ones we care about
		# Also gives a nice speed-up
		# Get paticles in disk
		if Lz_hat != None:
			zmag = np.dot(coords,Lz_hat)
			r_z = np.zeros(np.shape(coords))
			r_z[:,0] = zmag*Lz_hat[0]
			r_z[:,1] = zmag*Lz_hat[1]
			r_z[:,2] = zmag*Lz_hat[2]
			r_s = np.subtract(coords,r_z)
			smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
			in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
		# Get particles in sphere otherwise
		else:
			in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)


		T = gas_temp.gas_temperature(G)
		T = T[in_galaxy]
		M = G['m'][in_galaxy]

		dust_prod = calc_dust_acc(G,implementation=imp,, CNM_thresh=0.95, CO_frac=0.2, nano_iron=False, depletion=False)

		if depletion:
			DZ = (G['dz'][:,0]/(G['z'][:,0]+G['dz'][:,0]))[in_galaxy]
		else:
			DZ = (G['dz'][:,0]/G['z'][:,0])[in_galaxy]

		if imp == 'species':
			# First get silicates
			t_ref = 2.45E6*t_ref_factor;
			dust_formula_mass = 0.0
			atomic_mass = np.array([1.01, 2.0, 12.01, 14, 15.99, 20.2, 24.305, 28.086, 32.065, 40.078, 55.845])
			elem_num_dens = np.multiply(G['z'][in_galaxy,:len(atomic_mass)], G['rho'][in_galaxy, np.newaxis]*UnitDensity_in_cgs) / (atomic_mass*H_MASS)
			sil_elems_index = np.array([4,6,7,10]) # O,Mg,Si,Fe
			# number of atoms that make up one formula unit of silicate dust assuming an olivine, pyroxene mixture
			# with olivine fraction of 0.32 and Mg fraction of 0.8
			sil_num_atoms = np.array([3.63077,1.06,1.,0.570769]) # O, Mg, Si, Fe


			for k in range(4): dust_formula_mass += sil_num_atoms[k] * atomic_mass[sil_elems_index[k]];
			sil_num_dens = elem_num_dens[:,sil_elems_index] 
			# Find element with lowest number density factoring in number of atoms needed to make one formula unit of the dust species
			key = np.argmin(sil_num_dens / sil_num_atoms, axis = 1)
			key_num_dens = sil_num_dens[range(sil_num_dens.shape[0]),key]
			key_elem = sil_elems_index[key]
			key_DZ = G['dz'][in_galaxy,key_elem]/G['z'][in_galaxy,key_elem]
			key_M_dust = G['dz'][in_galaxy,key_elem]*M*1E10
			key_in_dust = sil_num_atoms[key]
			key_mass = atomic_mass[key_elem]
			cond_dens = 3.13
			growth_time = t_ref * key_in_dust * np.sqrt(key_mass) / dust_formula_mass * (cond_dens/3) * (1E-2/key_num_dens) * np.power(300/T,0.5)
			sil_dust_prod = (1.-key_DZ)*key_M_dust/growth_time
			sil_dust_prod[np.logical_or(key_DZ <= 0,key_DZ >= 1)] = 0.
			sil_dust_prod *= dust_formula_mass / atomic_mass[key_elem]
			sil_dust_prod[T>Tcut] = 0.

			# Now carbon dust
			CO_frac = 0.2; # Fraction of C locked in CO
			t_ref = 2.45E6*t_ref_factor
			key_elem = 2
			key_DZ = G['dz'][in_galaxy,key_elem]/((1-CO_frac)*G['z'][in_galaxy,key_elem])
			key_M_dust = G['dz'][in_galaxy,key_elem]*M*1E10
			key_in_dust = 1
			key_mass = atomic_mass[key_elem]
			dust_formula_mass = key_mass
			cond_dens = 2.25
			key_num_dens = elem_num_dens[:,key_elem]*(1-CO_frac)
			growth_time = t_ref * key_in_dust * np.sqrt(key_mass) / dust_formula_mass * (cond_dens/3) * (1E-2/key_num_dens) * np.power(300/T,0.5)
			carbon_dust_prod = (1.-key_DZ)*key_M_dust/growth_time
			carbon_dust_prod[np.logical_or(key_DZ <= 0,key_DZ >= 1)] = 0.
			carbon_dust_prod[T>Tcut] = 0.

			# Now iron dust
			t_ref = 2.45E6*t_ref_factor
			key_elem = 10
			key_DZ = G['dz'][in_galaxy,key_elem]/G['z'][in_galaxy,key_elem]
			key_M_dust = G['dz'][in_galaxy,key_elem]*M*1E10
			key_in_dust = 1
			dust_formula_mass = atomic_mass[key_elem]
			cond_dens = 7.86
			key_num_dens = elem_num_dens[:,key_elem]
			key_mass = atomic_mass[key_elem]
			growth_time = t_ref * key_in_dust * np.sqrt(key_mass) / dust_formula_mass * (cond_dens/3) * (1E-2/key_num_dens) * np.power(300/T,0.5)
			iron_dust_prod = (1.-key_DZ)*key_M_dust/growth_time
			iron_dust_prod[np.logical_or(key_DZ <= 0,key_DZ >= 1)] = 0.
			iron_dust_prod[T>Tcut] = 0.


		# Elemental implementation
		else:
			t_ref = 0.2E9*t_ref_factor; T_ref = 20; dens_ref = H_MASS;
			dens = G['rho'][in_galaxy]*UnitDensity_in_cgs
			growth_time = t_ref * (dens_ref/dens) * np.power(T_ref/T,0.5)
			sil_DZ = G['dz'][:,[4,6,7,10]][in_galaxy]/G['z'][:,[4,6,7,10]][in_galaxy]
			sil_DZ[np.logical_or(sil_DZ <= 0,sil_DZ >= 1)] = 1.
			sil_dust_mass = np.multiply(G['dz'][:,[4,6,7,10]][in_galaxy],M[:,np.newaxis]*1E10)
			sil_dust_prod = np.sum((1.-sil_DZ)*sil_dust_mass/growth_time[:,np.newaxis],axis=1)
			CO_frac = 0.2; # Fraction of C locked in CO
			C_DZ = G['dz'][:,2][in_galaxy]/((1-CO_frac)*G['z'][:,2][in_galaxy])
			C_dust_mass = G['dz'][:,2][in_galaxy]*M*1E10
			carbon_dust_prod = (1.-C_DZ)*C_dust_mass/growth_time
			carbon_dust_prod[np.logical_or(C_DZ <= 0,C_DZ >= 1)] = 0.
			iron_dust_prod = np.zeros(len(sil_dust_prod))


		axes.hist(nH, bins=np.logspace(np.log10(1E-2),np.log10(1E3),bin_nums), weights=sil_dust_prod, histtype='step', cumulative=True, label=labels[i], color=colors[i], \
			         linewidth=linewidths[0], linestyle=linestyles[0])
		axes.hist(nH, bins=np.logspace(np.log10(1E-2),np.log10(1E3),bin_nums), weights=carbon_dust_prod, histtype='step', cumulative=True, label=labels[i], color=colors[i], \
			         linewidth=linewidths[0], linestyle=linestyles[1])
		axes.hist(nH, bins=np.logspace(np.log10(1E-2),np.log10(1E3),bin_nums), weights=iron_dust_prod, histtype='step', cumulative=True, label=labels[i], color=colors[i], \
			         linewidth=linewidths[0], linestyle=linestyles[2])

	lines = []
	for i in range(len(labels)):
		lines += [mlines.Line2D([], [], color=colors[i], label=labels[i])]
	lines += [mlines.Line2D([], [], color='xkcd:black', linestyle =linestyles[0],label='Silicate'), \
		      mlines.Line2D([], [], color='xkcd:black', linestyle =linestyles[1],label='Carbon'), \
		      mlines.Line2D([], [], color='xkcd:black', linestyle =linestyles[2],label='Iron')]

	axes.legend(handles=lines,loc=2, frameon=False)
	axes.set_xlim([1E-2,1E3])
	xlabel = r'$n_H$ (cm$^{-3}$)'; ylabel = r'Cumulative Inst. Dust Prod. $(M_{\odot}/yr)$'
	plt_set.setup_labels(axes,xlabel,ylabel)
	if log:
		axes.set_yscale('log')
		axes.set_ylim([1E-3,1E1])
	axes.set_xscale('log')

	plt.savefig(foutname)
	plt.close()
"""




def dust_acc_diag(params, gas, header, center_list, r_max_list,  Lz_list=None, height_list=None, bin_nums=100, time=False, depletion=False, log = False, \
	           cosmological=True, Tmin=1, Tmax=1E5, Tcut=300, labels=None, foutname='dust_acc_diag.png', style='color', implementation='species', \
	           t_ref_factors = None):
	"""
	Make plot of instantaneous dust growth for a given snapshot depending on the dust evolution implementation used

	Parameters
	----------
	params : array
		List of parameters to plot diagnostics for (inst_dust_prod, growth_timescale, )
	gas : array
	    Array of snapshot gas data structure
	header : array
		Array of snapshot header structure
	bin_nums: int
		Number of bins to use
	time : bool, optional
		Print time in corner of plot (useful for movies)
	style : string
		Plotting style when plotting multiple data sets
		'color' - gives different color and linestyles to each data set
		'size' - make all lines solid black but with varying line thickness

	Returns
	-------
	None
	"""

	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(gas), style=style)

	# Set up subplots based on number of parameters given
	fig,axes = plt_set.setup_figure(len(params))

	for i,param in enumerate(params):
		axis = axes[i]
		if param == 'inst_dust_prod':
			plt_set.setup_axis(axis, 'nH', param)
		if param == 'g_timescale':
			plt_set.setup_axis(axis, param, 'g_timescale_frac')


		for j in range(len(gas)):

			if isinstance(implementation, list):
				imp = implementation[j]
			else:
				imp = implementation

			G = gas[j]; H = header[j]; center = center_list[j]; r_max = r_max_list[j];
			if Lz_list != None:
				Lz_hat = Lz_list[j]; disk_height = height_list[j];
			else:
				Lz_hat = None; disk_height = None;

			coords = np.copy(G['p']) # Since we edit coords need to make a deep copy
			coords -= center
			# Get only data of particles in sphere/disk since those are the ones we care about
			# Also gives a nice speed-up
			# Get paticles in disk
			if Lz_hat != None:
				zmag = np.dot(coords,Lz_hat)
				r_z = np.zeros(np.shape(coords))
				r_z[:,0] = zmag*Lz_hat[0]
				r_z[:,1] = zmag*Lz_hat[1]
				r_z[:,2] = zmag*Lz_hat[2]
				r_s = np.subtract(coords,r_z)
				smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
				in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
			# Get particles in sphere otherwise
			else:
				in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)


			T = gas_temp.gas_temperature(G)
			T = T[in_galaxy]
			M = G['m'][in_galaxy]

			if depletion:
				nH = G['rho']*UnitDensity_in_cgs * ( 1. - (G['z'][:,0]+G['z'][:,1]+G['dz'][:,0])) / H_MASS
			else:
				nH = G['rho']*UnitDensity_in_cgs * ( 1. - (G['z'][:,0]+G['z'][:,1])) / H_MASS

			if param == 'inst_dust_prod':
				weight_vals = calc_dust_acc(G,implementation=imp, CNM_thresh=1.0, CO_frac=0.2, nano_iron=False, depletion=False)
				x_vals = dict.fromkeys(weight_vals.keys(), nH)
			elif param == 'g_timescale':
				if imp == 'species':
					x_vals = calc_spec_acc_timescale(G, depletion=False, CNM_thresh=1.0, nano_iron=False)
				else:
					x_vals = calc_elem_acc_timescale(G)
				for key in x_vals.keys(): 
					x_vals[key]*=1E-9
				weight_vals=dict.fromkeys(x_vals.keys(), np.full(len(nH),1./len(nH)))
			else:
				print('%s is not a valid parameter for dust_growth_diag()'%param)
				return
			lines = []
			for k in range(len(labels)):
				lines += [mlines.Line2D([], [], color=colors[k], label=labels[k])]

			# Set up bins based on limits and scale of x axis
			limits = axis.get_xlim()
			scale_str = axis.get_xaxis().get_scale()
			if scale_str == 'log':
				bins = np.logspace(np.log10(limits[0]),np.log10(limits[1]),bin_nums)
			else:
				bins = np.linspace(limits[0],limits[1],bin_nums)

			for k,key in enumerate(sorted(weight_vals.keys())):
				axis.hist(x_vals[key][in_galaxy], bins=bins, weights=weight_vals[key][in_galaxy], histtype='step', cumulative=True, label=labels[j], color=colors[j], \
				         linewidth=linewidths[0], linestyle=linestyles[k])
				lines += [mlines.Line2D([], [], color='xkcd:black', linestyle =linestyles[k],label=key)]

		# Want legend only on first plot
			if i == 0:
				axis.legend(handles=lines,loc=2, frameon=False)


	plt.savefig(foutname)
	plt.close()






def binned_phase_plot(param, gas, header, center_list, r_max_list, Lz_list=None, height_list=None, bin_nums=100, time=False, depletion=False, cosmological=True, \
			   nHmin=1E-3, nHmax=1E3, Tmin=1E1, Tmax=1E5, numbins=200, thecmap='hot', vmin=1E-8, vmax=1E-4, labels =None, log=False, foutname='phase_plot.png'):
	"""
	Plots the temperate-density has phase

	Parameters
	----------
	param: string
		What parameterto bin 2d-historgram over
	gas : array
	    Array of snapshot gas data structure
	header : array
		Array of snapshot header structure
	bin_nums: int
		Number of bins to use
	depletion: bool, optional
		Was the simulation run with the DEPLETION option

	Returns
	-------
	None
	"""

	for i in range(len(gas)):
		G = gas[i]; H = header[i]; center = center_list[i]; r_max = r_max_list[i];
		if Lz_list != None:
			Lz_hat = Lz_list[i]; disk_height = height_list[i];
		else:
			Lz_hat = None; disk_height = None;

		coords = np.copy(G['p']) # Since we edit coords need to make a deep copy
		coords -= center
		# Get only data of particles in sphere/disk since those are the ones we care about
		# Also gives a nice speed-up
		# Get paticles in disk
		if Lz_hat != None:
			zmag = np.dot(coords,Lz_hat)
			r_z = np.zeros(np.shape(coords))
			r_z[:,0] = zmag*Lz_hat[0]
			r_z[:,1] = zmag*Lz_hat[1]
			r_z[:,2] = zmag*Lz_hat[2]
			r_s = np.subtract(coords,r_z)
			smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
			in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
		# Get particles in sphere otherwise
		else:
			in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

		if param == 'DZ':
			if depletion:
				values = (G['dz'][:,0]/(G['z'][:,0]+G['dz'][:,0]))[in_galaxy]
			else:
				values = (G['dz'][:,0]/G['z'][:,0])[in_galaxy]
			bar_label = 'D/Z Ratio in Pixel'
		else:
			print("Parameter given to binned_phase_plot is not supported:",param)
			return

		if depletion:
			nH = np.log10(G['rho']*UnitDensity_in_cgs * ( 1. - (G['z'][:,0]+G['z'][:,1]+G['dz'][:,0])) / H_MASS)[in_galaxy]
		else:
			nH = np.log10(G['rho']*UnitDensity_in_cgs * ( 1. - (G['z'][:,0]+G['z'][:,1])) / H_MASS)[in_galaxy]
		T = np.log10(gas_temp.gas_temperature(G))
		T = T[in_galaxy]
		M = G['m'][in_galaxy]

		# Bin data across nH and T parameter space
		nH_bins = np.linspace(np.log10(nHmin), np.log10(nHmax), numbins)
		T_bins = np.linspace(np.log10(Tmin), np.log10(Tmax), numbins)
		ret = binned_statistic_2d(nH, T, values, statistic=np.mean, bins=[nH_bins, T_bins])

		fig = plt.figure()
		ax = plt.gca()
		plt.subplot(111, facecolor='xkcd:black')
		if log:
			plt.imshow(ret.statistic.T, origin='bottom', cmap=plt.get_cmap(thecmap), norm=mpl.colors.LogNorm(), vmin=vmin, vmax=vmax, extent=[np.log10(nHmin),np.log10(nHmax),np.log10(Tmin),np.log10(Tmax)])
			#plt.hist2d(nH, T, range=np.log10([[nHmin,nHmax],[Tmin,Tmax]]), bins=numbins, cmap=plt.get_cmap(thecmap), norm=mpl.colors.LogNorm(), weights=weight, vmin=vmin, vmax=vmax) 
		else:
			plt.imshow(ret.statistic.T, origin='bottom', cmap=plt.get_cmap(thecmap), vmin=vmin, vmax=vmax, extent=[np.log10(nHmin),np.log10(nHmax),np.log10(Tmin),np.log10(Tmax)])
			#plt.hist2d(nH, T, range=np.log10([[nHmin,nHmax],[Tmin,Tmax]]), bins=numbins, cmap=plt.get_cmap(thecmap), weights=weight, vmin=vmin, vmax=vmax) 
		cbar = plt.colorbar()
		cbar.ax.set_ylabel(bar_label, fontsize=LARGE_FONT)


		plt.xlabel(r'log $n_{H} ({\rm cm}^{-3})$', fontsize=LARGE_FONT) 
		plt.ylabel(r'log T (K)', fontsize=LARGE_FONT)
		plt.tight_layout()
		if time:
			if cosmological:
				z = H['redshift']
				ax.text(.95, .95, 'z = ' + '%.2g' % z, color="xkcd:white", fontsize = 16, ha = 'right', transform=ax.transAxes)
			else:
				t = H['time']
				ax.text(.95, .95, 't = ' + '%2.1g Gyr' % t, color="xkcd:white", fontsize = 16, ha = 'right', transform=ax.transAxes)	
		plt.savefig(labels[i]+'_'+foutname)
		plt.close()




def calc_stellar_Rd(S, center, r_max, Lz_hat=None, disk_height=5, bin_nums=50):
	"""
	Calculate the stellar scale radius (Rd) for a galaxy given its star particles

	Parameters
	----------
	S : dict
	    Snapshot star data structure
	center : array
		3-D coordinate of center of circle
	r_max : double
		maximum radii of gas particles to use
	Lz_hat: array
		Unit vector of Lz to be used to mask only 
	disk_height: double
		Height of disk to mask if Lz_hat is given, default is 5 kpc
	bin_nums : int
		Number of bins to use
	Returns
	-------
	Rd : double
		Galactic stellar scale radius
	"""	

	coords = np.copy(S['p']) # Since we edit coords need to make a deep copy
	coords -= center
	# Get only data of particles in sphere/disk since those are the ones we care about
	# Also gives a nice speed-up
	# Get paticles in disk
	if Lz_hat != None:
		zmag = np.dot(coords,Lz_hat)
		r_z = np.zeros(np.shape(coords))
		r_z[:,0] = zmag*Lz_hat[0]
		r_z[:,1] = zmag*Lz_hat[1]
		r_z[:,2] = zmag*Lz_hat[2]
		r_s = np.subtract(coords,r_z)
		smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
		in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
	# Get particles in sphere otherwise
	else:
		in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

	M = S['m'][in_galaxy]*1E10
	coords = coords[in_galaxy]

	r_bins = np.linspace(0, r_max, num=bin_nums)
	r_vals = (r_bins[1:] + r_bins[:-1]) / 2.
	surf_dens = np.zeros(bin_nums-1)

	for j in range(bin_nums-1):
		# find all coordinates within shell
		r_min = r_bins[j]; r_max = r_bins[j+1];
		annulus_area = np.pi * np.power((r_max-r_min)*1000,2) # pc^2

		zmag = np.dot(coords,Lz_hat)
		r_z = np.zeros(np.shape(coords))
		r_z[:,0] = zmag*Lz_hat[0]
		r_z[:,1] = zmag*Lz_hat[1]
		r_z[:,2] = zmag*Lz_hat[2]
		r_s = np.subtract(coords,r_z)
		smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
		in_annulus = np.where((np.abs(zmag) <= disk_height) & (smag <= r_max) & (smag > r_min))

		surf_dens[j] = np.sum(M[in_annulus]) / annulus_area

	# Now fit 
	fit,_ = curve_fit(dens_profile_func, r_vals, surf_dens)
	cent_surf = fit[1]
	Rd = fit[0]

	print("Rd = %e, cent. surf. dens. = %e" % (Rd,cent_surf))
	
	return Rd


def dens_profile_func(radius, Rd, cent_surf):
	return cent_surf * np.exp(-radius/Rd)


def dust_data_vs_time(params, param_lims, implementation='species', datanames=['data.pickle'], data_dir='data/', foutname='dust_data_vs_time.png', \
	                     labels=None, time=False, cosmological=True, log=True, std_bars=True, style='color'):
	"""
	Plots all time averaged data vs time from precompiled data for a set of simulation runs

	Parameters
	----------
	dataname : list
		List of data file names for sims
	datadir: str
		Directory of data
	foutname: str
		Name of file to be saved

	Returns
	-------
	None
	"""

	species_names = ['Silicates','Carbon','SiC','Iron','O Reservoir']
	source_names = ['Accretion','SNe Ia', 'SNe II', 'AGB']

	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(datanames), style=style)

	# Set up subplots based on number of parameters given
	fig,axes = plt_set.setup_figure(len(params))

	for i, y_param in enumerate(params):
		# Set up for each plot
		axis = axes[i]
		y_lim = param_lims[i]
		if time:
			x_param = 'time'
		else:
			x_param = 'redshift'
		plt_set.setup_axis(axis, x_param, y_param, y_lim=y_lim)

		param_labels=None
		if y_param == 'DZ':
			param_id = 'DZ_ratio'
		elif y_param == 'source_frac':
			param_id = 'source_frac'
			param_labels = ['Accretion','SNe Ia', 'SNe II', 'AGB']
		elif y_param=='spec_frac':
			param_id = 'spec_frac'
			if implementation == 'species':
				param_labels = ['Silicates','Carbon','SiC','Iron','O Bucket']
			else:
				param_labels = ['Silicates','Carbon']
		elif y_param == 'Si/C':
			param_id = 'sil_to_C_ratio'
		else:
			print("%s is not a valid parameter for dust_data_vs_time()\n"%y_param)
			return()

		for j,dataname in enumerate(datanames):
			with open(data_dir+dataname, 'rb') as handle:
				data = pickle.load(handle)

			if cosmological:
				if time:
					time_data = data['time']
				else:
					time_data = -1.+1./data['a_scale']
			else:
				time_data = data['time']

			# Check if parameter has subparameters
			if param_labels == None:
				mean_vals = data[param_id][:,0]; std_vals = data[param_id][:,1:];
				axis.plot(time_data, mean_vals, color='xkcd:black', linestyle=LINE_STYLES[j], label=labels[j], zorder=3)
				if std_bars:
					axis.fill_between(time_data, std_vals[:,0], std_DZ[:,1], alpha = 0.3, color='xkcd:black', zorder=1)
			else:
				mean_vals = data[param_id][:,:,0]; std_vals = data[param_id][:,:,1:];
				for k in range(np.shape(mean_vals)[1]):
					axis.plot(time_data, mean_vals[:,k], color=LINE_COLORS[k], linestyle=LINE_STYLES[j], zorder=3)
					if std_bars:
						axis.fill_between(time_data, std_vals[:,k,0], std_DZ[:,k,1], alpha = 0.3, color=LINE_COLORS[k], zorder=1)
		# Only need to label the seperate simulations in the first plot
		if i==0 and len(datanames)>1:
			axis.legend(loc=0, frameon=False, fontsize=SMALL_FONT)
		# If there are subparameters need to make their own legend
		if param_labels != None:
			param_lines = []
			for j, label in enumerate(param_labels):
				param_lines += [mlines.Line2D([], [], color=LINE_COLORS[j], label=label)]
			axis.legend(handles=param_lines, loc=0, frameon=False, fontsize=SMALL_FONT)
		if log:
			axis.set_xlim(time_data[1],time_data[-1])
	plt.tight_layout()
	plt.savefig(foutname)
	plt.close()


def compile_dust_data(snap_dir, foutname='data.pickle', data_dir='data/', mask=False, halo_dir='', Rvir_frac = 1., \
                      r_max = None, Lz_hat = None, disk_height = None, overwrite=False, cosmological=True, startnum=0, \
                      endnum=600, implementation='species', depletion=False):
	"""
	Compiles all the dust data needed for time evolution plots from all of the snapshots 
	into a small file.

	Parameters
	----------
	snap_dir : string
		Name of directory with snapshots to be used 

	Returns
	-------
	None

	"""

	if os.path.isfile(data_dir + foutname) and not overwrite:
		"Data exists already. \n If you want to overwrite it use the overwrite param."
	else:
		# First create ouput directory if needed
		try:
			# Create target Directory
			os.mkdir(data_dir)
			print("Directory ", data_dir, " Created")
		except:
			print("Directory ", data_dir, " already exists")


		print("Fetching data now...")
		length = endnum-startnum+1
		# Need to load in the first snapshot to see how many dust species there are
		if implementation=='species':
			G = readsnap(snap_dir, startnum, 0, cosmological=cosmological)
			if G['k']==-1:
				print("No snapshot found in directory")
				print("Snap directory:", snap_dir)
				return
			species_num = np.shape(G['spec'])[1]
			print("There are %i dust species"%species_num)
		else:
			species_num = 2
		# Most data comes with mean of values and 16th and 84th percentile
		DZ_ratio = np.zeros([length,3])
		sil_to_C_ratio = np.zeros([length,3])
		sfr = np.zeros(length)
		metallicity = np.zeros([length,3])
		time = np.zeros(length)
		a_scale = np.zeros(length)
		source_frac = np.zeros((length,4,3))
		spec_frac = np.zeros((length,species_num,3))


		# Go through each of the snapshots and get the data
		for i, num in enumerate(range(startnum, endnum+1)):
			print(num)
			G = readsnap(snap_dir, num, 0, cosmological=cosmological)
			H = readsnap(snap_dir, num, 0, header_only=True, cosmological=cosmological)
			S = readsnap(snap_dir, num, 4, cosmological=cosmological)

			if G['k']==-1:
				print("No snapshot found in directory")
				print("Snap directory:", snap_dir)
				return

			if mask:
				coords = G['p']
				center = np.zeros(3)
				if cosmological:
					halo_data = Table.read(halo_dir,format='ascii')
					# Convert to physical units
					xpos =  halo_data['col7'][num-1]*H['time']/H['hubble']
					ypos =  halo_data['col8'][num-1]*H['time']/H['hubble']
					zpos =  halo_data['col9'][num-1]*H['time']/H['hubble']
					rvir = halo_data['col13'][num-1]*H['time']/H['hubble']
					
					#TODO : Add ability to only look at particles in disk using angular momentum vector from
					# halo file
					
					center = np.array([xpos,ypos,zpos])
					coords -= center
					if r_max == None:
						print("Using AHF halo as spherical mask with radius of ",str(Rvir_frac)," * Rvir.")
						r_max = rvir*Rvir_frac
					else:
						print("Using AHF halo as spherical mask with radius of ",str(r_max)," kpc.")

					in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)
				else:
					if r_max == None:
						print("Must give maximum radius r_max for non-cosmological simulations!")
						return
					# Recenter coords at center of periodic box
					boxsize = H['boxsize']
					mask1 = coords > boxsize/2; mask2 = coords <= boxsize/2
					coords[mask1] -= boxsize/2; coords[mask2] += boxsize/2;
					center = np.average(coords, weights = G['m'], axis = 0)
					coords -= center
					# Check if mask should be sphere or disk if Lz_hat is given it's a disk
					if Lz_hat != None:
						zmag = np.dot(coords,Lz_hat)
						r_z = np.zeros(np.shape(coords))
						r_z[:,0] = zmag*Lz_hat[0]
						r_z[:,1] = zmag*Lz_hat[1]
						r_z[:,2] = zmag*Lz_hat[2]
						r_s = np.subtract(coords,r_z)
						smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
						in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
					# Get particles in sphere otherwise
					else:
						in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

				for key in G.keys():
					if key != 'k':
						G[key] = G[key][in_galaxy]
				# Check if there are any star particles
				if S['k']!=-1:
					coords = S['p']
					if not cosmological:
						boxsize = H['boxsize']
						mask1 = coords > boxsize/2; mask2 = coords <= boxsize/2
						coords[mask1] -= boxsize/2; coords[mask2] += boxsize/2;

					coords -= center

					# Check if mask should be sphere or disk if Lz_hat is given it's a disk
					if Lz_hat != None:
						zmag = np.dot(coords,Lz_hat)
						r_z = np.zeros(np.shape(coords))
						r_z[:,0] = zmag*Lz_hat[0]
						r_z[:,1] = zmag*Lz_hat[1]
						r_z[:,2] = zmag*Lz_hat[2]
						r_s = np.subtract(coords,r_z)
						smag = np.sqrt(np.sum(np.power(r_s,2),axis=1))
						in_galaxy = np.logical_and(np.abs(zmag) <= disk_height, smag <= r_max)
					# Get particles in sphere otherwise
					else:
						in_galaxy = np.sum(np.power(coords,2),axis=1) <= np.power(r_max,2.)

					S['age'] = S['age'][in_galaxy]
					S['m'] = S['m'][in_galaxy]

			M = G['m']
			omeganot = H['omega0']
			h = H['hubble']
			if cosmological:
				a_scale[i] = H['time']
				time[i] = tfora(H['time'], omeganot, h)
			else:
				time[i] = H['time']

			if depletion:
				metallicity[i] = weighted_percentile(G['z'][:,0]+G['dz'][:,0], weights=M)
			else:
				metallicity[i] = weighted_percentile(G['z'][:,0], weights=M)

			for j in range(4):
				source_frac[i,j] = weighted_percentile(G['dzs'][:,j], weights=M)
				source_frac[i,j][source_frac[i,j]==0] = EPSILON


			if implementation == 'species':
				# Need to mask all rows with nan and inf values for average to work
				for j in range(species_num):
					spec_frac_vals = G['spec'][:,j]/G['dz'][:,0]
					is_num = np.logical_and(~np.isnan(spec_frac_vals), ~np.isinf(spec_frac_vals))
					spec_frac[i,j] = weighted_percentile(spec_frac_vals[is_num], weights =M[is_num])
					spec_frac[i,j][spec_frac[i,j]==0] = EPSILON

				sil_to_C_vals = G['spec'][:,0]/G['spec'][:,1]
				is_num = np.logical_and(~np.isnan(sil_to_C_vals), ~np.isinf(sil_to_C_vals))
				sil_to_C_ratio[i] = weighted_percentile(sil_to_C_vals[is_num], weights =M[is_num])
				sil_to_C_ratio[i][sil_to_C_ratio[i]==0] = EPSILON

			elif implementation == 'elemental':
				# Need to mask nan and inf values for average to work
				spec_frac_vals = (G['dz'][:,4]+G['dz'][:,6]+G['dz'][:,7]+G['dz'][:,10])/G['dz'][:,0]
				is_num = np.logical_and(~np.isnan(spec_frac_vals), ~np.isinf(spec_frac_vals))
				spec_frac[i,0] = weighted_percentile(spec_frac_vals[is_num], weights =M[is_num])
				spec_frac[i,0][spec_frac[i,0]==0] = EPSILON

				spec_frac_vals = G['dz'][:,2]/G['dz'][:,0]
				is_num = np.logical_and(~np.isnan(spec_frac_vals), ~np.isinf(spec_frac_vals))
				spec_frac[i,1] = weighted_percentile(spec_frac_vals[is_num], weights =M[is_num])
				spec_frac[i,1][spec_frac[i,1]==0] = EPSILON

				sil_to_C_vals = (G['dz'][:,4]+G['dz'][:,6]+G['dz'][:,7]+G['dz'][:,10])/G['dz'][:,2]
				is_num = np.logical_and(~np.isnan(sil_to_C_vals), ~np.isinf(sil_to_C_vals))
				sil_to_C_ratio[i] = weighted_percentile(sil_to_C_vals[is_num], weights =M[is_num])
				sil_to_C_ratio[i][sil_to_C_ratio[i]==0] = EPSILON

			if depletion:
				DZ_vals = G['dz'][:,0]/(G['z'][:,0]+G['dz'][:,0])
			else:
				DZ_vals = G['dz'][:,0]/G['z'][:,0]
			DZ_ratio[i] = weighted_percentile(DZ_vals, weights=M)
			DZ_ratio[i][DZ_ratio[i]==0] = EPSILON

			# Calculate SFR as all stars born within the last 100 Myrs
			if S['k']!=-1:
				if cosmological:
					formation_time = tfora(S['age'], omeganot, h)
					current_time = time[i]
				else:
					formation_time = S['age']*UnitTime_in_Gyr
					current_time = time[i]*UnitTime_in_Gyr

				time_interval = 100E-3 # 100 Myr
				new_stars = (current_time - formation_time) < time_interval
				sfr[i] = np.sum(S['m'][new_stars]) * UnitMass_in_Msolar / (time_interval*1E9)   # Msun/yr

		if cosmological:
			data = {'time':time,'a_scale':a_scale,'DZ_ratio':DZ_ratio,'sil_to_C_ratio':sil_to_C_ratio,'metallicity':metallicity,'source_frac':source_frac,'spec_frac':spec_frac,'sfr':sfr}
		else:
			data = {'time':time,'DZ_ratio':DZ_ratio,'sil_to_C_ratio':sil_to_C_ratio,'metallicity':metallicity,'source_frac':source_frac,'spec_frac':spec_frac,'sfr':sfr}
		with open(data_dir+foutname, 'wb') as handle:
			pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)


def compare_dust_creation(Z_list, dust_species, data_dirc, FIRE_ver=2, transition_age = 0.03753, style='color'):
	"""
	Plots comparison of stellar dust creation for the given stellar metallicities

	Parameters
	----------
	Z_list : list
		List of metallicities to compare in solar units
	dust_species : list
		List of dust species to plot individually (carbon, silicates, iron, SiC, silicates+)
	data_dirc: string
		Name of directory to store calculated yields files
	FIRE_ver : int
		Version of FIRE metals yields to use in calculations
	transition_age : double
		Age at which stellar yields switch from O/B to AGB stars

	Returns
	-------
	None

	"""

	# First create ouput directory if needed
	try:
	    # Create target Directory
	    os.mkdir(data_dirc)
	    print("Directory " + data_dirc +  " Created")
	except:
	    print("Directory " + data_dirc +  " already exists")

	# Get plot stylization
	linewidths,colors,linestyles = plt_set.setup_plot_style(len(Z_list), style=style)

	N = 10000 # number of steps 
	max_t = 10. # max age of stellar population to compute yields

	time_step = max_t/N
	time = np.arange(0,max_t,time_step)

	# First make simulated data if it hasn't been made already
	for Z in Z_list:
		name = '/elem_Z_'+str(Z).replace('.','-')+'_cum_yields.pickle'
		if not os.path.isfile(data_dirc + name):
			cum_yields, cum_dust_yields, cum_species_yields = totalStellarYields(max_t,N,Z, routine="elemental")
			pickle.dump({"time": time, "yields": cum_yields, "elem": cum_dust_yields, "spec": cum_species_yields}, open(data_dirc + name, "wb" ))

		name = '/spec_Z_'+str(Z).replace('.','-')+'_cum_yields.pickle'
		if not os.path.isfile(data_dirc +name):
			cum_yields, cum_dust_yields, cum_species_yields = totalStellarYields(max_t,N,Z, routine="species")
			pickle.dump({"time": time, "yields": cum_yields, "elem": cum_dust_yields, "spec": cum_species_yields}, open(data_dirc + name, "wb" ))


	# Compare routine carbon yields between routines
	# Set up subplots based on number of parameters given
	fig,axes = plt_set.setup_figure(len(dust_species))
	x_param = 'time'; y_param = 'cum_dust_prod'
	x_lim = [0,max_t]

	for i, species in enumerate(dust_species):
		axis = axes[i]
		plt_set.setup_axis(axis, x_param, y_param, x_lim=x_lim)
		if species == 'carbon':
			name = 'Carbonaceous'
			indices = np.array([1])
		elif species == 'silicates':
			name = 'Silicates'
			indices = np.array([0])
		elif species == 'silicates+':
			name = 'Silicates+Others'
			indices = np.array([0,2,3])
		elif species == 'iron':
			name = 'Iron'
			indices = np.array([3])
		elif species == 'SiC':
			name = 'SiC'
			indices = np.array([2])
		else:
			print("%s is not a valid dust species for compare_dust_creation()\n"%species)
			return()

		# Add extra lines emphazising the time regimes for SNe II or AGB+SNe Ia
		axis.axvline(transition_age, color='xkcd:grey',lw=3)
		# Only need labels and legend for first plot
		if i == 0:
			y_arrow = 1E-5
			axis.annotate('AGB+SNe Ia', va='center', xy=(transition_age, y_arrow), xycoords="data", xytext=(2*transition_age, y_arrow), 
			            arrowprops=dict(arrowstyle='<-',color='xkcd:grey', lw=3), size=LARGE_FONT, color='xkcd:grey')
			axis.annotate('SNe II', va='center', xy=(transition_age, y_arrow/2), xycoords="data", xytext=(0.2*transition_age, y_arrow/2), 
			            arrowprops=dict(arrowstyle='<-',color='xkcd:grey', lw=3), size=LARGE_FONT, color='xkcd:grey')
			# Make legend
			lines = []
			for j in range(len(Z_list)):
				lines += [mlines.Line2D([], [], color=colors[j], label=r'Z = %.2g $Z_{\odot}$' % Z_list[j])]
			lines += [mlines.Line2D([], [], color='xkcd:black', linestyle=linestyles[0], label='Elemental'), mlines.Line2D([], [], color='xkcd:black', linestyle=linestyles[1],label='Species')]
			axis.legend(handles=lines, frameon=True, ncol=2, loc='center left', bbox_to_anchor=(0.025,1.0), framealpha=1, fontsize=SMALL_FONT)
		#  Add label for dust species
		axis.text(.95, .05, name, color="xkcd:black", fontsize = LARGE_FONT, ha = 'right', transform=axis.transAxes)

		for j,Z in enumerate(Z_list):
			name = '/elem_Z_'+str(Z).replace('.','-')+'_cum_yields.pickle'
			data = pickle.load(open(data_dirc + name, "rb" ))
			time = data['time']; cum_yields = data['yields']; cum_dust_yields = data['elem']; cum_species_yields = data['spec'];
			elem_cum_spec = np.sum(cum_species_yields[:,indices], axis=1)
			axis.loglog(time, elem_cum_spec, color = colors[j], linestyle = linestyles[0], nonposy = 'clip', linewidth = linewidths[j])

			name = '/spec_Z_'+str(Z).replace('.','-')+'_cum_yields.pickle'
			data = pickle.load(open(data_dirc + name, "rb" ))
			time = data['time']; cum_yields = data['yields']; cum_dust_yields = data['elem']; cum_species_yields = data['spec'];
			spec_cum_spec = np.sum(cum_species_yields[:,indices], axis=1)
			axis.loglog(time, spec_cum_spec, color = colors[j], linestyle = linestyles[1], nonposy = 'clip', linewidth = linewidths[j])

		axis.set_ylim([1E-7,1E-2])
		axis.set_xlim([time[0], time[-1]])

	plt.savefig('creation_routine_comparison.pdf', format='pdf', transparent=False, bbox_inches='tight')
	plt.close()