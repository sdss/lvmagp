import asyncio
from typing import Tuple, TYPE_CHECKING, Any, Optional

from photutils.background import Background2D, MedianBackground

from lvmagp.images import Image
from .background import Background


class DaophotBackground(Background):
    """
    Daophot class for background.

       https://photutils.readthedocs.io/en/stable/background.html

    """

    __module__ = "lvmagp.images.processors.background"

    def __init__(self, *, box_size=(50, 50), **kwargs):

        """Initializes the wrapper.

Parameters:

    box_size int or array_like (int)

        The box size along each axis. If box_size is a scalar then a square box of size box_size will be used. If box_size has two elements, they must be in (ny, nx) order. For best results, the box shape should be chosen such that the data are covered by an integer number of boxes in both dimensions. When this is not the case, see the edge_method keyword for more options.

    maskarray_like (bool), optional

        A boolean mask, with the same shape as data, where a True value indicates the corresponding element of data is masked. Masked data are excluded from calculations. mask is intended to mask sources or bad pixels. Use coverage_mask to mask blank areas of an image. mask and coverage_mask differ only in that coverage_mask is applied to the output background and background RMS maps (see fill_value).

    coverage_maskarray_like (bool), optional

        A boolean mask, with the same shape as data, where a True value indicates the corresponding element of data is masked. coverage_mask should be True where there is no coverage (i.e., no data) for a given pixel (e.g., blank areas in a mosaic image). It should not be used for bad pixels (in that case use mask instead). mask and coverage_mask differ only in that coverage_mask is applied to the output background and background RMS maps (see fill_value).

    fill_value float, optional

        The value used to fill the output background and background RMS maps where the input coverage_mask is True.

    exclude_percentile float in the range of [0, 100], optional

        The percentage of masked pixels in a box, used as a threshold for determining if the box is excluded. If a box has more than exclude_percentile percent of its pixels masked then it will be excluded from the low-resolution map. Masked pixels include those from the input mask and coverage_mask, those resulting from the data padding (i.e., if edge_method='pad'), and those resulting from sigma clipping (if sigma_clip is used). Setting exclude_percentile=0 will exclude boxes that have any masked pixels. Note that completely masked boxes are always excluded. For best results, exclude_percentile should be kept as low as possible (as long as there are sufficient pixels for reasonable statistical estimates). The default is 10.0.

    filter_size int or array_like (int), optional

        The window size of the 2D median filter to apply to the low-resolution background map. If filter_size is a scalar then a square box of size filter_size will be used. If filter_size has two elements, they must be in (ny, nx) order. filter_size must be odd along both axes. A filter size of 1 (or (1, 1)) means no filtering.

    filter_thresholdint, optional

        The threshold value for used for selective median filtering of the low-resolution 2D background map. The median filter will be applied to only the background boxes with values larger than filter_threshold. Set to None to filter all boxes (default).

    edge_method{‘pad’, ‘crop’}, optional

        The method used to determine how to handle the case where the image size is not an integer multiple of the box_size in either dimension. Both options will resize the image for internal calculations to give an exact multiple of box_size in both dimensions.

            'pad': pad the image along the top and/or right edges. This is the default and recommended method. Ideally, the box_size should be chosen such that an integer number of boxes is only slightly larger than the data size to minimize the amount of padding.

            'crop': crop the image along the top and/or right edges. This method should be used sparingly. Best results will occur when box_size is chosen such that an integer number of boxes is only slightly smaller than the data size to minimize the amount of cropping.

    sigma_clipastropy.stats.SigmaClip instance, optional

        A SigmaClip object that defines the sigma clipping parameters. If None then no sigma clipping will be performed. The default is to perform sigma clipping with sigma=3.0 and maxiters=10.

    bkg_estimatorcallable, optional

        A callable object (a function or e.g., an instance of any BackgroundBase subclass) used to estimate the background in each of the boxes. The callable object must take in a 2D ndarray or MaskedArray and have an axis keyword. Internally, the background will be calculated along axis=1 and in this case the callable object must return a 1D ndarray, where np.nan values are used for masked pixels. If bkg_estimator includes sigma clipping, it will be ignored (use the sigma_clip keyword here to define sigma clipping). The default is an instance of SExtractorBackground.

    bkgrms_estimatorcallable, optional

        A callable object (a function or e.g., an instance of any BackgroundRMSBase subclass) used to estimate the background RMS in each of the boxes. The callable object must take in a 2D ndarray or MaskedArray and have an axis keyword. Internally, the background RMS will be calculated along axis=1 and in this case the callable object must return a 1D ndarray, where np.nan values are used for masked pixels. If bkgrms_estimator includes sigma clipping, it will be ignored (use the sigma_clip keyword here to define sigma clipping). The default is an instance of StdBackgroundRMS.

    interpolatorcallable, optional

        A callable object (a function or object) used to interpolate the low-resolution background or background RMS image to the full-size background or background RMS maps. The default is an instance of BkgZoomInterpolator, which uses the scipy.ndimage.zoom function.

        """

        self.box_size=box_size
        self.kwargs=kwargs
        self.kwargs["bkg_estimator"] = MedianBackground()
        self.kwargs["filter_size"] = (3, 3)

    def __call__(self, image: Image, *, box_size=None, **kwargs):

        """return given image substracted.

        Args:
            image: Image.

        Returns:
            Background in float.
        """

        return Background2D(image.data,
                           box_size if box_size else self.box_size,
                           **{**self.kwargs, **kwargs}).background



__all__ = ["DaophotBackground"]
