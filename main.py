import cv2
import numpy as np
import sys
from matplotlib import pyplot as plt
import math

refPt = []
cropping = False

# function for labelling object 
def click_and_crop(event, x, y, flags, param):

	# grab references to the global variables
	global refPt, cropping

	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates and indicate that cropping is being
	# performed
	if event == cv2.EVENT_LBUTTONDOWN:
		refPt = [(x, y)]
		cropping = True
 
	# check to see if the left mouse button was released
	elif event == cv2.EVENT_LBUTTONUP:
		# record the ending (x, y) coordinates and indicate that
		# the cropping operation is finished
		refPt.append((x, y))
		cropping = False
 		
		# draw a rectangle around the region of interest
		cv2.rectangle(img_copy, refPt[0], refPt[1], (0, 255, 0), 2)
		cv2.imshow("image", img_copy)

def feature_images(input_image) :

	'''function for computing the 49 feature images.
	   Any output pixel=R*a+G*b+B*c and contains only linearly independent combinations
	   a,b,c belongs to {-2,-1,0,1,2}.Also, {0,0,0} not allowed
	   input : input image
	   returns a list of all images'''

	image=input_image
	# Now, for all the feature spaces(49 in total..considering linear combinations of R,G,B values)

	feature_spaces=np.array([(1,1,1),(2,2,1),(1,1,0),(2,2,-1),(1,1,-1),(2,1,2),(2,1,1),(2,1,0),(2,1,-1),(2,1,-2),(1,0,1),(2,0,1),(1,0,0),
	(2,0,-1),(1,0,-1),(2,-1,2),(2,-1,1),(2,-1,0),(2,-1,-1),(2,-1,-2),(1,-1,1),(2,-2,1),(1,-1,0),(2,-2,-1),(1,-1,-1),(1,2,2),(1,2,1),(1,2,0),
	(1,2,-2),(1,2,-1),(1,1,2),(1,1,-2),(1,0,2),(1,0,-2),(1,-1,2),(1,-1,-2),(1,-2,2),(1,-2,1),(1,-2,0),(1,-2,-1),(1,-2,-2),(0,1,1)
	,(0,2,1),(0,1,0),(0,2,-1),(0,1,-1),(0,1,2),(0,1,-2),(0,0,1)])
	max_possible=[]
	min_possible=[]
    # iterating for each feature space
	for i,feature in enumerate(feature_spaces) :
		maximum = max(0,feature[0])*255 + max(0,feature[1])*255 +max(0,feature[2])*255
		minimum = min(0,feature[0])*255 + min(0,feature[1])*255 +min(0,feature[2])*255
		max_possible.append(maximum)
		min_possible.append(minimum)

	h,w,c=image.shape
	new_image=np.array((h,w))
	image=image.astype('uint32')
	feature_images_list=[]
	for i in range(0,49) :
		range_=max_possible[i]-min_possible[i]
		new_image= ((image[:,:,0]*feature_spaces[i][0]+image[:,:,1]*feature_spaces[i][1]+image[:,:,2]*feature_spaces[i][2]-min_possible[i])*255)/range_
		new_image=new_image.astype('uint8')
		feature_images_list.append(new_image)

	return feature_images_list

def likelihood(img,obj_img,bg_img) :

	#img is the feature image
	'''input : feature image, labelled object, background images
	   returns likelihood image and variance'''
	global h_,w_   
	
	h,w=bg_img.shape
	bg_img[h_:h-h_,w_:w-w_] = 0  #segmenting surrounding from object pixels

	hist_obj = cv2.calcHist([obj_img],[0],None,[32],[0,256])
	hist_bg  = cv2.calcHist([bg_img],[0],None,[32],[0,256])
	hist_bg[0]=hist_bg[0]- sum(hist_obj) # for removing the effect of the dark pixels in the object region 

	#plotting object and background
	#plt.plot(hist_bg,color='b',label="background")
	#plt.plot(hist_obj,color='r',label="object")
	#plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=2, mode="expand", borderaxespad=0.)
	#plt.show()

	# delta for avoiding divide by zero and zero in the logarithm
	delta=np.ones((32,1))*.0001

	#normalizing the histograms
	#p for object and q for object
	p=hist_obj/sum(hist_obj)
	q=hist_bg/sum(hist_bg)

	p=p.ravel()
	q=q.ravel()
	delta=delta.ravel()

	# defining the log likelihood
	temp1=np.maximum(p,delta)
	temp2=np.maximum(q,delta)
	L = np.log10(temp1)-np.log10(temp2)
    # compute variance
	VR_intra1 = variance(L,p)
	VR_intra2 = variance(L,q)
	VR_inter = variance(L,(p+q)/2)
	VR = VR_inter/(VR_intra1+VR_intra2)
	print "variance=",VR
	#plotting likelihood
	#plt.figure()
	x=[0,35]
	y=[127,127]
	#plt.plot(x,y,color='black')
	#plt.plot(L)
	#plt.show()
	# for creating likelihood image
	L_=((L+4)*255)/8 
	print L_
	'''for i in range(32) :
		if L_[i]>127 :
			L_[i]=255
		elif L_[i]<127 :
			L_[i]=0
		else :
			L_[i]=127'''
				
	img=img/8
	likelihood_img=L_[img]  # creating likelihood image

	#cv2.imshow("like",likelihood_img)
	#cv2.waitKey(0)

	return likelihood_img,VR

def variance(L,a) :

	# computes variance of a distribition with pdf=a
	temp1=np.sum(np.multiply(np.multiply(L,L),a))
	temp2=np.sum(np.multiply(a,L))
	temp2=temp2*temp2
	var=temp1-temp2
	#print temp1,temp2,"temp variance",a

	return var


if __name__ == "__main__":
	argument=sys.argv
	
	if (len(argument)<2) :
		print "\n \n provide an image as input\n\n"

		image=cv2.imread("cliffjump.jpg")
	if (len(argument)==2):	
		image=cv2.imread(str(argument[1])) # complete image of the scene

	clone=image.copy()
	img_copy=image.copy()
	cv2.namedWindow("image")
	cv2.setMouseCallback("image", click_and_crop)

	print "Label the object"
	print "After making a bounding box, press 'c' "
	print "if you wish to select the object again, press 'r' "

	# keep looping until the 'c' key is pressed
	while True:
		# display the image and wait for a keypress
		cv2.imshow("image", img_copy)
		key = cv2.waitKey(1) & 0xFF
	 
		# if the 'r' key is pressed, reset the cropping region
		if key == ord("r"):
			image = clone.copy()
			img_copy=image.copy()
	 
		# if the 'c' key is pressed, break from the loop
		elif key == ord("c"):
			break
	 
	# if there are two reference points, then crop the region of interest
	# from the image and display it
	if len(refPt) == 2:
		roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
		cv2.imshow("ROI", roi)
		print "press any key"
		cv2.waitKey(0)
	 
	# close all open windows
	cv2.destroyAllWindows()


	obj_img=roi  # roi containing the object
	h,w,c=obj_img.shape
	h_=int(h*0.3)
	w_=int(w*0.3)

	bg_img_original= clone[refPt[0][1]-h_:refPt[1][1]+h_, refPt[0][0]-w_:refPt[1][0]+w_]   # roi containing object and surroundings

	cv2.rectangle(clone, refPt[0], refPt[1], (0, 255, 0), 2)
	cv2.rectangle(clone, (refPt[0][0]-w_,refPt[0][1]-h_), (refPt[1][0]+w_,refPt[1][1]+h_), (0, 255, 0), 2)
	cv2.imshow("image_clone", clone)
	print "press any key"
	cv2.waitKey(0)
	cv2.destroyAllWindows()
	cv2.imshow("see",image)

	list_feature_images=feature_images(image)
	list_object_images =feature_images(obj_img)
	list_bg_images     =feature_images(bg_img_original)
	list_VR=[]
	list_likelihood_images=[]

	for i in range(49) :

		likelihood_image,VR = likelihood(list_feature_images[i],list_object_images[i],list_bg_images[i])
		list_VR.append(VR)
		list_likelihood_images.append(likelihood_image)
		

	sorted_VR=sorted(range(len(list_VR)),key=lambda x:list_VR[x],reverse=True)
	print list_VR
	print sorted_VR

	array=np.array(sorted_VR)
	array1=np.array(list_VR)
	print array1[array]

	fig = plt.figure(figsize=(20,10))
	fig.suptitle('likelihood images according to variance ratio values', fontsize=14, fontweight='bold')

	for i in range(49):
		plt.subplot(7,7,i+1)
		plt.imshow(list_likelihood_images[sorted_VR[i]],cmap='gray')
		plt.axis('off')

	#plt.subplot_tool()
	plt.show()
	fig.savefig("result.png")
