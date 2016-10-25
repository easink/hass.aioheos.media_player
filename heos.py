"""
Denon Heos notification service.
"""
from heos import Heos, HeosException

import logging
import voluptuous as vol

        # PLATFORM_SCHEMA, SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK,
        # SUPPORT_TURN_OFF, SUPPORT_TURN_ON, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET,

from homeassistant.components.media_player import (
        PLATFORM_SCHEMA, MEDIA_TYPE_MUSIC,
        SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET, SUPPORT_VOLUME_STEP,
        SUPPORT_STOP, SUPPORT_PAUSE, SUPPORT_PLAY_MEDIA,
        SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK,
        MediaPlayerDevice)
from homeassistant.const import (CONF_HOST, CONF_NAME,
        STATE_IDLE, STATE_PAUSED, STATE_PLAYING, STATE_UNKNOWN, STATE_OFF)
import homeassistant.helpers.config_validation as cv

# REQUIREMENTS = ['https://github.com/easink/heos/archive/v0.1.4.zip#heos==0.1.4']
REQUIREMENTS = ['git+https://github.com/easink/heos@dev#egg-heos',
                'lxml', 'httplib2']

DEFAULT_NAME = 'HEOS Player'

SUPPORT_HEOS = SUPPORT_STOP | SUPPORT_PAUSE | SUPPORT_PLAY_MEDIA | \
        SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET

# SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK | \

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discover_info=None):
    """Setup the HEOS platform."""

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    heos = HeosMediaPlayer(host, name)
    if heos:
        add_devices([heos])
        return True
    else:
        return False


class HeosMediaPlayer(MediaPlayerDevice):
    """ The media player ."""

    def __init__(self, host, name):
        """Initialize"""
        if host is None:
            _LOGGER.info('No host provided, will try to discover...')
        self._heos = Heos(host, verbose=True)
        self._heos.close()
        self._name = name
        self._volume = 0
        self._muted = 'off'
        self._mediasource = ''
        self._state = STATE_UNKNOWN
        self._media_artist = ''
        self._media_album = ''
        self._media_title = ''
        self._media_image_url = ''
        self._media_id = ''

        self.update()

    def update(self):
        """Retrieve latest state."""
        self._heos.connect()

        self._get_playing_media()
        self._state = self._heos.get_play_state()
        self._volume = self._heos.get_volume()
        self._muted = self._heos.get_mute_state()

        self._heos.close()
        return True

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def volume_level(self):
        """Volume level of the device (0..1)."""
        return int(self._volume) / 100.0

    @property
    def state(self):
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
        return self._media_artist

    @property
    def media_title(self):
        """Album name of current playing media."""
        return self._media_title

    @property
    def media_album_name(self):
        """Album name of current playing media."""
        return self._media_album

    @property
    def media_image_url(self):
        """Return the image url of current playing media."""
        return self._media_image_url

    @property
    def media_content_id(self):
        """Return the content ID of current playing media."""
        return self._media_id

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        if self._muted == 'on':
            return True
        else:
            return False

    def mute_volume(self, mute):
        """Mute volume"""
        self._heos.connect()
        self._heos.toggle_mute()
        self._heos.close()
        self.update_ha_state()

    def _get_playing_media(self):
        reply = self._heos.get_now_playing_media()
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

    # @property
    # def media_duration(self):
    #     """Duration of current playing media in seconds."""
    #     return self._media_duration

    # def media_next_track(self):
    #     """Go TO next track."""
    #     self._heos.connect()
    #     self._heos.play_next()
    #     self._heos.close()

    # def media_next_track(self):
    #     """Go TO next track."""
    #     self._heos.connect()
    #     self._heos.play_prev()
    #     self._heos.close()

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_HEOS

    # def turn_off(self):
    #     """Turn off media player."""

    # def volume_up(self):
    #     """Volume up media player."""
    #     # self._heos.connect()
    #     # self._heos.volume_level_up()
    #     # self._heos.close()
    #     pass

    # def volume_down(self):
    #     """Volume down media player."""
    #     # self._heos.connect()
    #     # self._heos.volume_level_down()
    #     # self._heos.close()
    #     pass

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._heos.connect()
        # 60 of 100 will be max
        self._heos.set_volume(volume * 100)
        self._heos.close()

    def media_play(self):
        """Play media player."""
        self._heos.connect()
        self._heos.play()
        self._heos.close()
        self.update_ha_state()

    def media_stop(self):
        """Stop media player."""
        self._heos.connect()
        self._heos.stop()
        self._heos.close()
        self.update_ha_state()

    def media_pause(self):
        """Pause media player."""
        self._heos.connect()
        self._heos.pause()
        self._heos.close()
        self.update_ha_state()

    # def media_next_track(self):
    #     """Send the next track command."""

    # def media_previous_track(self):
    #     """Send the previous track command."""
