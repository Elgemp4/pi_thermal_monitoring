import cv2
import numpy as np


class ImageProcessor:
    camera_width : int = 256 
    camera_height : int = 192 

    scale : int = 1 #scale multiplier
    alpha : float = 1.0 # Contrast control (1.0-3.0)
    colormap_index : int = 0
    font : int = cv2.FONT_HERSHEY_SIMPLEX
    dispFullscreen : bool = False
    rad : int = 0 #blur radius
    threshold :int = 2

    colormaps = [('Jet', cv2.COLORMAP_JET),
                ('Hot', cv2.COLORMAP_HOT),
                ('Magma', cv2.COLORMAP_MAGMA),
                ('Inferno', cv2.COLORMAP_INFERNO),
                ('Plasma', cv2.COLORMAP_PLASMA),
                ('Bone', cv2.COLORMAP_BONE),
                ('Spring', cv2.COLORMAP_SPRING),
                ('Autumn', cv2.COLORMAP_AUTUMN),
                ('Viridis', cv2.COLORMAP_VIRIDIS),
                ('Parula', cv2.COLORMAP_PARULA)]
    
    def get_width(self) -> int:
        return self.camera_width * self.scale

    def get_height(self) -> int:
        return self.camera_height * self.scale

    def apply_color_map(self, im_data) -> np.ndarray:
        bgr = cv2.cvtColor(im_data, cv2.COLOR_YUV2BGR_YUYV)
        bgr = cv2.convertScaleAbs(bgr, alpha=self.alpha)#Contrast

        bgr = cv2.resize(bgr, (self.get_width(), self.get_height()), interpolation=cv2.INTER_CUBIC)#Scale up!
        if self.rad>0:
            bgr = cv2.blur(bgr,(self.rad,self.rad))

        colormap_title, colormap = self.colormaps[self.colormap_index]
        heatmap_image = cv2.applyColorMap(bgr, colormap)
        return heatmap_image