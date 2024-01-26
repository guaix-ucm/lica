
# ----------------------
# Module utility classes
# ----------------------

class Point:
	""" Point class represents and manipulates x,y coords. """

	PATTERN = r'\((\d+),(\d+)\)'

	@classmethod
	def from_string(cls, point_str):
		pattern = re.compile(Point.PATTERN)
		matchobj = pattern.search(Roi_str)
		if matchobj:
			x = int(matchobj.group(1))
			y = int(matchobj.group(2))
			return cls(x,y)
		else:
			return None

	def __init__(self, x=0, y=0):
		""" Create a new point at the origin """
		self.x = x
		self.y = y

	def __add__(self, Roi):
		return NotImplementedError

	def __repr__(self):
		return f"({self.x},{self.y})"

class NormRoi:
	'''Normalized Roiangle with 0..1 floating point coordinates and dimensions'''
	def __init__(self, n_x0=None ,n_y0=None, n_width=1.0, n_height=1.0): 
		self.x0 = n_x0
		self.y0 = n_y0
		self.width = n_width
		self.height = n_height

	def __repr__(self):
		return f"[P0=({self.x0:s},{self.y0:s}) DIM=({self.width:.f} x {self.height:.f})]"

class Roi:
	""" Region of interest """

	PATTERN = r'\[(\d+):(\d+),(\d+):(\d+)\]' # NumPy style [row0:row1,col0:col1] 

	@classmethod
	def from_string(cls, Roi_str):
		'''numpy sections style'''
		pattern = re.compile(Roi.PATTERN)
		matchobj = pattern.search(Roi_str)
		if matchobj:
			y0 = int(matchobj.group(1))
			y1 = int(matchobj.group(2))
			x0 = int(matchobj.group(3))
			x1 = int(matchobj.group(4))
			return cls(x0,x1,y0,y1)
		else:
			return None

	@classmethod
	def from_normalized_roi(cls, width, height, n_roi, already_debayered=True):
		if n_roi.x0 is not None and n_roi.x0 + n_roi.width > 1.0:
			raise ValueError(f"normalized x0(={n_roi.x0}) + width(={n_roi.width}) = {n_roi.x0 + n_roi.width} exceeds 1.0")
		if n_roi.y0 is not None and n_roi.y0 + n_roi.height > 1.0:
			raise ValueError(f"normalized x0(={n_roi.y0}) + width(={n_roi.height}) = {n_roi.y0 + n_roi.height} exceeds 1.0")
		# If not already_debayered, we'll adjust to each image plane dimensions
		if not already_debayered:
			height = height //2  
			width  = width  //2 
		# From normalized ROI to actual image dimensions ROI
		w = int(width * n_roi.width) 
		h = int(height * n_roi.height)
		x0 = (width  - w)//2 if n_roi.x0 is None else int(width * n_roi.x0)
		y0 = (height - h)//2 if n_roi.y0 is None else int(height * n_roi.y0)
		return cls(x0, x0+w ,y0, y0+h)

	@classmethod
	def from_dict(cls, Roi_dict):
		return cls(Roi_dict['x0'], Roi_dict['x1'],Roi_dict['y0'], Roi_dict['y1'])
	
	def __init__(self, x0 ,x1, y0, y1):        
		self.x0 = min(x0,x1)
		self.y0 = min(y0,y1)
		self.x1 = max(x0,x1)
		self.y1 = max(y0,y1)

	def to_dict(self):
		return {'x0':self.x0, 'y0':self.y0, 'x1':self.x1, 'y1':self.y1}
		
	def xy(self):
		'''To use when displaying Roiangles in matplotlib'''
		return(self.x0, self.y0)

	def width(self):
		return abs(self.x1 - self.x0)

	def height(self):
		return abs(self.y1 - self.y0)
		
	def dimensions(self):
		'''returns width and height'''
		return abs(self.x1 - self.x0), abs(self.y1 - self.y0)

	def __add__(self, point):
		return Roi(self.x0 + point.x, self.x1 + point.x, self.y0 + point.y, self.y1 + point.y)

	def __radd__(self, point):
		return self.__add__(point)
		
	def __repr__(self):
		'''string in NumPy section notation'''
		return f"[{self.y0}:{self.y1},{self.x0}:{self.x1}]"
	  