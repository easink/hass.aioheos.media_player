"""
Denon Heos notification service.
"""
import asyncio

import logging
import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA, MEDIA_TYPE_MUSIC,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET, SUPPORT_VOLUME_STEP,
    SUPPORT_STOP, SUPPORT_PAUSE, SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK, SUPPORT_SEEK,
    SUPPORT_PLAY, MediaPlayerDevice)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_PAUSED, STATE_PLAYING, STATE_UNKNOWN, STATE_OFF)
import homeassistant.helpers.config_validation as cv

# REQUIREMENTS = ['https://github.com/easink/aioheos/archive/v0.0.1.zip#aioheos==0.0.1']
# REQUIREMENTS = ['git+https://github.com/easink/aioheos.git@v0.0.1#egg-aioheos==0.0.1',
# REQUIREMENTS = ['https://github.com/easink/aioheos/archive/master.zip#aioheos==0.0.1',
REQUIREMENTS = ['https://github.com/easink/aioheos/archive/v0.1.2.zip#aioheos==0.1.2']

DEFAULT_NAME = 'HEOS Player'

SUPPORT_HEOS = SUPPORT_PLAY | SUPPORT_STOP | SUPPORT_PAUSE | SUPPORT_PLAY_MEDIA | \
        SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | \
        SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | SUPPORT_SEEK

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

_LOGGER = logging.getLogger(__name__)

from aioheos import AioHeos, AioHeosException

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discover_info=None):
    """Setup the HEOS platform."""

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    heos = HeosMediaPlayer(hass, host, name)
    yield from heos.heos.connect(
        host=host,
        trigger_callback=heos.async_update_ha_state
        )

    yield from async_add_devices([heos])
    return True


class HeosMediaPlayer(MediaPlayerDevice):
    """ The media player ."""

    def __init__(self, hass, host, name):
        """Initialize"""
        if host is None:
            _LOGGER.info('No host provided, will try to discover...')
        self._hass = hass
        self.heos = AioHeos(loop=hass.loop, host=host, verbose=True)
        self._name = name
        # self.update()
        self._state = None
        self._media_artist = ''
        self._media_album = ''
        self._media_title = ''
        self._media_image_url = ''
        self._media_id = ''

    @asyncio.coroutine
    def async_update(self):
        """Retrieve latest state."""
        self.heos.request_play_state()
        self.heos.request_mute_state()
        self.heos.request_volume()
        self.heos.request_now_playing_media()
        return True

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def volume_level(self):
        """Volume level of the device (0..1)."""
        volume = self.heos.get_volume()
        return float(volume) / 100.0

    @property
    def state(self):
        self._state = self.heos.get_play_state()
        if self._state == 'stop':
            return STATE_OFF
        elif self._state == 'pause':
            return STATE_PAUSED
        elif self._state == 'play':
            return STATE_PLAYING
        else:
            return STATE_UNKNOWN

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    def media_artist(self):
        """Artist of current playing media."""
        return self.heos.get_media_artist()

    @property
    def media_title(self):
        """Album name of current playing media."""
        return self.heos.get_media_song()

    @property
    def media_album_name(self):
        """Album name of current playing media."""
        return self.heos.get_media_album()

    @property
    def media_image_url(self):
        """Return the image url of current playing media."""
        return self.heos.get_media_image_url()

    @property
    def media_content_id(self):
        """Return the content ID of current playing media."""
        return self.heos.get_media_id()

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        muted_state = self.heos.get_mute_state()
        if muted_state == 'on':
            return True
        else:
            return False

    @asyncio.coroutine
    def async_mute_volume(self, mute):
        """Mute volume"""
        self.heos.toggle_mute()

    def _get_playing_media(self):
        reply = self.heos.get_now_playing_media()
        # {
        #   "type" : "'song'",
        #   "song": "'song name'",
        #   "album": "'album name'",
        #   "artist": "'artist name'",
        #   "image_url": "'image url'",
        #   "mid": "'media id'",
        #   "qid": "'queue id'",
        #   "sid": source_id
        #   "album_id": "Album Id'"
        # }
        if 'artist' in reply.keys():
            self._media_artist = reply['artist']
        if 'album' in reply.keys():
            self._media_album = reply['album']
        if 'song' in reply.keys():
            self._media_title = reply['song']
        if 'image_url' in reply.keys():
            self._media_image_url = reply['image_url']
        if 'mid' in reply.keys():
            self._media_id = reply['mid']

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self.heos.get_duration()/1000.0

    @property
    def media_position_updated_at(self):
        return self.heos.get_position_updated_at()

    @property
    def media_position(self):
        return self.heos.get_position()/1000.0

    @asyncio.coroutine
    def async_media_next_track(self):
        """Go TO next track."""
        self.heos.request_play_next()

    @asyncio.coroutine
    def async_media_previous_track(self):
        """Go TO previous track."""
        self.heos.request_play_previous()

    @asyncio.coroutine
    def async_media_seek(self, position):
        """Seek to posistion."""
        print('MEDIA SEEK', position)

    @property
    def supported_features(self):
        """Flag of media commands that are supported."""
        return SUPPORT_HEOS

    @asyncio.coroutine
    def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        # 60 of 100 will be max
        self.heos.set_volume(volume * 100)

    @asyncio.coroutine
    def async_media_play(self):
        """Play media player."""
        self.heos.play()
        # self.update_ha_state()

    @asyncio.coroutine
    def async_media_stop(self):
        """Stop media player."""
        self.heos.stop()
        # self.update_ha_state()

    @asyncio.coroutine
    def async_media_pause(self):
        """Pause media player."""
        self.heos.pause()
        # self.update_ha_state()

    @asyncio.coroutine
    def async_media_play_pause(self):
        """Play or pause the media player."""
        if self._state == 'play':
            self.media_pause()
        else:
            self.media_play()
