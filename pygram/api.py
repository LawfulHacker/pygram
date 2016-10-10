#!coding:utf-8

from datetime import datetime
import itertools
import cookielib
import requests
import atexit
import signal
import pickle
import random
import time
import json
import os

class LoginException(Exception):
    pass


class InvalidDataException(Exception):
    pass


class PyGram(object):

    """
    PyGram API. This is an unofficial version that uses login and password.

    login = your instagram login
    password = your instagram password

    https://github.com/moacirmoda/pygram
    """

    user_agent = ("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36")
    accept_language = 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4'

    user_id = 0
    media_by_tag = 0
    login_status = False
    s = requests.Session()
    is_logged = False

    url = 'https://www.instagram.com/'
    url_tag = 'https://www.instagram.com/explore/tags/%s/'
    url_likes = 'https://www.instagram.com/web/likes/%s/like/'
    url_unlike = 'https://www.instagram.com/web/likes/%s/unlike/'
    url_comment = 'https://www.instagram.com/web/comments/%s/add/'
    url_follow = 'https://www.instagram.com/web/friendships/%s/follow/'
    url_unfollow = 'https://www.instagram.com/web/friendships/%s/unfollow/'
    url_login = 'https://www.instagram.com/accounts/login/ajax/'
    url_logout = 'https://www.instagram.com/accounts/logout/'
    url_media_detail = 'https://www.instagram.com/p/%s/?__a=1'
    url_user_detail = 'https://www.instagram.com/%s/?__a=1'

    def __init__(self, login, password):
        """Initialize the api."""
        self.user_login = login.lower()
        self.user_password = password

        self.s = self.get_session()
        if not self.is_logged:
            self.login()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.persist_session()

    def login(self):
        """Login on the instagram platform."""
        self.s.cookies.update({'sessionid': '', 'mid': '', 'ig_pr': '1',
                               'ig_vw': '1920', 'csrftoken': '',
                               's_network': '', 'ds_user_id': ''})

        self.login_post = {'username': self.user_login,
                           'password': self.user_password}

        self.s.headers.update({'Accept-Encoding': 'gzip, deflate',
                               'Accept-Language': self.accept_language,
                               'Connection': 'keep-alive',
                               'Content-Length': '0',
                               'Host': 'www.instagram.com',
                               'Origin': 'https://www.instagram.com',
                               'Referer': 'https://www.instagram.com/',
                               'User-Agent': self.user_agent,
                               'X-Instagram-AJAX': '1',
                               'X-Requested-With': 'XMLHttpRequest'})

        r = self.s.get(self.url)
        self.s.headers.update({'X-CSRFToken': r.cookies['csrftoken']})
        time.sleep(5 * random.random())
        login = self.s.post(self.url_login, data=self.login_post,
                            allow_redirects=True)
        self.s.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        self.csrftoken = login.cookies['csrftoken']
        time.sleep(5 * random.random())

        if login.status_code == 200:
            r = self.s.get('https://www.instagram.com/')
            finder = r.text.find(self.user_login)
            if finder != -1:
                self.user = User(self.get_user_id_by_login(self.user_login))
                self.is_logged = True
            else:
                raise InvalidDataException
        else:
            raise LoginException

    def logout(self):
        """Logout from the Instagram platform."""
        logout_post = {'csrfmiddlewaretoken': self.csrftoken}
        request = self.s.post(self.url_logout, data=logout_post)

        if request.status_code == 200:
            return True
        return False

    def get_session_filename(self):
        dir = '/tmp/pygram-sessions'
        os.system('mkdir -p %s' % dir)
        filename = os.path.join(dir, datetime.now().strftime("%Y%m%d"))
        return filename

    def get_session(self):
        filename = self.get_session_filename()
        if os.path.exists(filename):
            session = requests.session()
            session.cookies = cookielib.LWPCookieJar(filename=filename)
            session.cookies.load()

            r = session.get(self.url)
            session.headers.update({'X-CSRFToken': r.cookies['csrftoken']})

            self.is_logged = True
            return session

        return requests.Session()

    def persist_session(self):
        filename = self.get_session_filename()
        if not os.path.exists(filename):
            jar = cookielib.LWPCookieJar(filename=filename)
            for c in self.s.cookies:
                print c
                jar.set_cookie(c)
            jar.save(ignore_discard=True)

    def get_user_id_by_login(self, user_name):
        url_info = self.url_user_detail % (user_name)
        info = self.s.get(url_info)
        all_data = json.loads(info.text)
        id_user = all_data['user']['id']
        return id_user

    def get_medias_by_tag(self, tag):
        """Get media ID set, by your hashtag."""
        url_tag = self.url_tag % tag
        r = self.s.get(url_tag)
        text = r.text

        finder_text_start = ('<script type="text/javascript">window._sharedData = ')
        finder_text_start_len = len(finder_text_start) - 1
        finder_text_end = ';</script>'

        all_data_start = text.find(finder_text_start)
        all_data_end = text.find(finder_text_end, all_data_start + 1)
        json_str = text[(all_data_start + finder_text_start_len + 1):all_data_end]
        all_data = json.loads(json_str)

        return [Media(item) for item in list(all_data['entry_data']['TagPage'][0]['tag']['media']['nodes'])]

    def like(self, media):
        """Send http request to like media by object."""
        url_likes = self.url_likes % (media.id)
        request = self.s.post(url_likes)

        if request.status_code == 200:
            return True
        return False

    def unlike(self, media):
        """Send http request to unlike media by ID."""
        url_unlike = self.url_unlike % (media.id)
        request = self.s.post(url_unlike)

        if request.status_code == 200:
            return True
        return False

    def follow(self, user):
        """Send http request to follow."""
        url_follow = self.url_follow % (user.id)
        request = self.s.post(url_follow)

        if request.status_code == 200:
            return True
        return False


class Base(object):

    def __init__(self, dic):
        self.__dict = dic

    def __getattr__(self, name):
        try:
            return self.__dict[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    @property
    def obj(self):
        return self.__dict


class Media(Base):

    def __init__(self, dic, *args, **kwargs):
        dic['owner'] = User(dic['owner'])
        super(Media, self).__init__(dic, *args, **kwargs)

    @property
    def url(self):
        return "https://www.instagram.com/p/%s/" % self.code


class User(Base):

    url_user_detail = 'https://www.instagram.com/%s/?__a=1'

    def __init__(self, dic, *args, **kwargs):
        super(User, self).__init__(dic, *args, **kwargs)
