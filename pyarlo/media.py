# coding: utf-8
"""Implementation of Arlo Media object."""
import logging
from datetime import datetime
from datetime import timedelta
from pyarlo.const import LIBRARY_ENDPOINT, PRELOAD_DAYS
from pyarlo.utils import http_get

_LOGGER = logging.getLogger(__name__)


class ArloMediaLibrary(object):
    """Arlo Library Media module implementation."""

    def __init__(self, arlo_session, preload=True, days=PRELOAD_DAYS):
        """Initialiaze Arlo Media Library object.

        :param arlo_session: PyArlo shared session
        :param preload: Boolean to pre-load video library.
        :param days: If preload, number of days to lookup.

        :returns ArloMediaLibrary object
        """
        self._session = arlo_session

        if preload and days:
            self.videos = self.load(days)
        else:
            self.videos = []

    def __repr__(self):
        """Representation string of object."""
        return "<{0}: {1}>".format(self.__class__.__name__,
                                   self._session.userid)

    def load(self, days, date_from=None, date_to=None):
        """Load  Arlo videos from the given criteria

        :param date_from: refine from initial date
        :param date_to: refine final date
        """
        videos = []
        url = LIBRARY_ENDPOINT
        if not (date_from and date_to):
            now = datetime.today()
            date_from = (now - timedelta(days=days)).strftime('%Y%m%d')
            date_to = now.strftime('%Y%m%d')

        params = {'dateFrom': date_from, 'dateTo': date_to}
        data = self._session.query(url,
                                   method='POST',
                                   extra_params=params).get('data')

        # get all cameras to append to create ArloVideo object
        cameras = self._session.cameras

        for video in data:
            # pylint: disable=cell-var-from-loop
            srccam = \
                list(filter(
                    lambda cam: cam.device_id == video.get('deviceId'),
                    cameras))[0]
            videos.append(ArloVideo(video, srccam, self._session))
        _LOGGER.debug("Total loaded videos (%s) - %s", len(videos), videos)
        return videos


class ArloVideo(object):
    """Object for Arlo Video file."""

    def __init__(self, attrs, camera, arlo_session):
        """Initialiaze Arlo Video object.

        :param attrs: Video attributes
        :param camera: Arlo camera which recorded the video
        :param arlo_session: Arlo shared session
        """
        self._attrs = attrs
        self._camera = camera
        self._session = arlo_session

    def __repr__(self):
        """Representation string of object."""
        return "<{0}: {1}>".format(self.__class__.__name__, self._name)

    @property
    def _name(self):
        """Define object name."""
        return "{0}_{1}: {2}".format(
            self._camera.name,
            self.id,
            self._attrs.get('mediaDuration'))

    # pylint: disable=invalid-name
    @property
    def id(self):
        """Return object id."""
        return self._attrs.get('name')

    @property
    def content_type(self):
        """Return content_type."""
        return self._attrs.get('contentType')

    @property
    def camera(self):
        """Return camera object that recorded video."""
        return self._camera

    @property
    def media_duration_seconds(self):
        """Return media duration in seconds."""
        return self._attrs.get('mediaDurationSecond')

    @property
    def triggered_by(self):
        """Return the reason why video was recorded."""
        return self._attrs.get('reason')

    @property
    def thumbnail_url(self):
        """Return thumbnail url."""
        return self._attrs.get('presignedThumbnailUrl')

    @property
    def video_url(self):
        """Return video content url."""
        return self._attrs.get('presignedContentUrl')

    def download_thumbnail(self, filename=None):
        """Download JPEG thumbnail.

        :param filename: File to save thumbnail. Default: stdout
        """
        return http_get(self.thumbnail_url, filename)

    def download_video(self, filename=None):
        """Download video content.

        :param filename: File to save video. Default: stdout
        """
        return http_get(self.video_url, filename)

# vim:sw=4:ts=4:et:
