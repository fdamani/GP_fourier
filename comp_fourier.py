import numpy as np
import warnings

from . import mkcovs, kron_ops
from . import fft_ops as rffb


def conv_fourier(x,dims,minlens,nxcirc = None,condthresh = 1e8):
	# Compute least-squares regression sufficient statistics in DFT basis
	# Version of this NOT complete for higher dimensions 9/15/17!
	#
	# INPUT:
	# -----
	#           x [D x n x p] - stimulus, where each row vector is the spatial stim at a single time, D is number of batch
	#        dims [m x 1] - number of coefficients along each stimulus dimension
	#     minlens [m x 1] - minimum length scale for each dimension (can be scalar)
	#      nxcirc [m x 1] - circular boundary in each stimulus dimension (minimum is dims) OPTIONAL
	#  condthresh [1 x 1] - condition number for thresholding for small eigenvalues OPTIONAL
	#
	# OUTPUT:
	# ------
	#     Bx  - output data, x, in fourier domain
	#  wwnrm [nf x 1] - squared "effective frequencies" in vector form for each dim
	#   Bfft  {1 x p} - cell array with DFT bases for each dimension
	# 	1e8 is default value (condition number on prior covariance)


	dims = np.array(np.reshape(dims,(1,-1)))
	minlens = np.array(np.reshape(minlens,(1,-1)))

	# Set circular bounardy (for n-point fft) to avoid edge effects, if needed
	if nxcirc is None:
	    #nxcirc = np.ceil(max([dims(:)'+minlens(:)'*4; dims(:)'*1.25]))'
	    nxcirc = np.ceil(np.max(np.concatenate((dims+minlens*4 ,dims), axis = 0), axis = 0))


	nd = np.size(dims) # number of filter dimensions
	if np.size(minlens) is 1 and nd is not 1: #% make vector out of minlens, if necessary
	    minlens = np.repmat(minlens,nd,1)


	# Loop through dimensions

	#None of these quantities depend on the data directly
	wvecs = [rffb.comp_wvec(nxcirc[jj],minlens[0][jj], condthresh) for jj in np.arange(nd)]
	#cdiagvecs = [mkcovs.mkcovdiag_ASD(minlens[jj],1,nxcirc[jj],np.square(wvecs[jj]))  for jj in np.arange(nd)]
	Bffts = [rffb.realfftbasis(dims[jj],nxcirc[jj],wvecs[jj])[0] for jj in np.arange(nd)]


	#Note... These previous lines could have been done with one function...mkcovs.mkcov_ASDfactored, but due to ease of eye
	# and a desire to use list comprehensions, each component is split into it's own function. This also allows for an
	#easier tracking of each individual part, should you need to follow the steps....


	#fprintf('\n Total # Fourier coeffs represented: %d\n\n', prod(ncoeff));

	def f(switcher):  
	    # switch based on stimulus dimension
	    if switcher is 2:
	    	pass
	    if switcher is 3:
	    	pass
	    return{
	    1: #% 1 dimensional stimulus
	         [np.square(2*np.pi/nxcirc[0]) * np.square(wvecs[0]), #normalized wvec
	         np.ones([np.size(wvecs[0]),1])==1] #indices to keep 

	        
	    # 2: % 2 dimensional stimulus
	        
	    #     % Form full frequency vector and see which to cut
	    #     Cdiag = kron(cdiagvecs{2},cdiagvecs{1});
	    #     ii = (Cdiag/max(Cdiag))>1/condthresh; % indices to keep 
	                    
	    #     % compute vector of normalized frequencies squared
	    #     [ww1,ww2] = ndgrid(wvecs{1},wvecs{2});
	    #     wwnrm = [(ww1(ii)*(2*pi/nxcirc(1))).^2 ...
	    #         (ww2(ii)*(2*pi/nxcirc(2))).^2];
	        
	    # 3: % 3 dimensional stimulus

	    #     Cdiag = kron(cdiagvecs{3},(kron(cdiagvecs{2},cdiagvecs{1})));
	    #     ii = (Cdiag/max(Cdiag))>1/condthresh; % indices to keep
	        
	    #     % compute vector of normalized frequencies squared
	    #     [ww1,ww2,ww3] = ndgrid(wvecs{1},wvecs{2},wvecs{3});
	    #     wwnrm = [(ww1(ii)*(2*pi/nxcirc(1))).mv ^2, ...
	    #         (ww2(ii)*(2*pi/nxcirc(2))).^2, ....,
	    #         (ww3(ii)*(2*pi/nxcirc(3))).^2];
	        
	    # otherwise
	    #     error('compLSsuffstats_fourier.m : doesn''t yet handle %d dimensional filters\n',nd);
		}[switcher] 
	try:
	    [wwnrm, ii] = f(nd)
	except KeyError:
	    print('\n\n Does not handle values of dimension', nd, 'yet')    
	

	# Calculate stimulus sufficient stats in Fourier domain

	
	# if x.shape[0] == 1: 

	# 	#originally this used the transpose operation (kronmulttrp) ! !!!might be a transpositional issue.
	# 	Bx = kron_ops.kronmult(Bffts,np.transpose(x)) # convert to Fourier domain
	# 	Bx = Bx[ii] # prune unneeded freqs

	# elif x.shape[0]>1: #Batched data. when the shape of x is 3 and dims is 2, for example. 

	Bx = [kron_ops.kronmult(Bffts,np.transpose(batch)) for batch in x]
	Bx = [prune[ii] for prune in Bx]

	return Bx, wwnrm, Bffts, ii, nxcirc, wvecs




def conv_fourier_mult_neuron(x,dims,minlens,num_neurons,nxcirc = None,condthresh = 1e8):


	Bys = np.array(conv_fourier(x[:,0,:],dims,minlens,nxcirc = None,condthresh = 1e8)[0])
	N_four = Bys.shape[1]
	if num_neurons >1:
		for i in np.arange(1,num_neurons):
			Bys = np.vstack((Bys,conv_fourier(x[:,i,:],dims,minlens,nxcirc = None,condthresh = 1e8)[0]))
	Bys = np.reshape(Bys, [x.shape[0],num_neurons,N_four])
	[wwnrm, Bffts, ii, nxcirc, wvecs] = conv_fourier(x[:,0,:],dims,minlens,nxcirc = None,condthresh = 1e8)[1:]
	return Bys, wwnrm, Bffts, ii, nxcirc, wvecs




def conv_fourier_batch(x,dims,minlens,nxcirc = None,condthresh = 1e8):

	if len(x.shape) <= len(dims):
		warnings.warn('\n\n shape of input vector is not longer than dims vector. Try using conv_fourier, not conv_fourier_batch \n\n')

	#return a list of arrays for the Bx all the batched data, 	
	return [conv_fourier(batch,dims,minlens,nxcirc,condthresh)[0] 
	for batch in arange(x)] + [conv_fourier(x[0],dims,minlens,nxcirc,condthresh)[1,:]]




def compLSsuffstats_fourier(x,y,dims,minlens,nxcirc = None,condthresh = 1e8):
	# Compute least-squares regression sufficient statistics in DFT basis
	if nxcirc is None:
		nxcirc = dims

	[By, wwnrm, Bffts, ii, nxcirc, wvecs] = conv_fourier(y,dims,minlens,condthresh = condthresh)

	y = np.reshape(y,[1,-1])
	dd = {}
	dd['x'] = Bffts[0]@x.T
	dd['xx'] = dd['x']@dd['x'].T
	dd['xy'] = dd['x'] @ y.T
	# Fill in other statistics
	dd['yy'] = y@y.T# marginal response variance

	return dd, By, wwnrm, Bffts, ii, nxcirc, wvecs









