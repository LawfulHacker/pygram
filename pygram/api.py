#!coding:utf-8

import requests
import random
import time
import json
import atexit
import signal
import itertools


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

    url = 'https://www.instagram.com/'
    url_tag = 'https://www.instagram.com/explore/tags/%s/?__a=1'
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

    def login(self):

        if self.login_status:
            return True

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
                self.user = self.get_user_id_by_login(self.user_login)
                self.login_status = True
                return self.login_status
            else:
                print (r.text)
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

    def get_user_id_by_login(self, user_name):
        url_info = self.url_user_detail % (user_name)
        info = self.s.get(url_info)
        all_data = json.loads(info.text)
        id_user = all_data['user']['id']
        return id_user

    def get_medias_to_collect_by_tags(self, tags, *args, **kwargs):
        tag = random.choice(tags)
        return self.get_medias_to_collect_by_tag(tag, *args, **kwargs)

    def get_medias_to_collect_by_tag(self, tag, total=None, min_likes=None, max_likes=None):
        """Get media ID set, by your hashtag."""
        url_tag = self.url_tag % tag
        r = self.s.get(url_tag)

        medias = []
        for media in r.json()['tag']['top_posts']['nodes'] + r.json()['tag']['media']['nodes']:
            if 'code' in media.keys():
                media = self.s.get(self.url_media_detail % (media['code']))
                media = media.json()['media']
                if 'code' in media.keys():

                    media = Media(media)
                    if len(medias) >= total:
                        break

                    # se a midia tiver menos que o configurado, passa
                    if min_likes and media.likes['count'] < min_likes:
                        continue

                    # se a midia tiver mais que o configurado, passa
                    if max_likes and media.likes['count'] > max_likes:
                        continue

                    medias.append(media)

        return medias

    def like(self, media_id):
        """Send http request to like media by object."""
        if self.login():
            url_likes = self.url_likes % (media_id)
            request = self.s.post(url_likes)

            if request.status_code == 200:
                return True
        return False

    def unlike(self, media_id):
        """Send http request to unlike media by ID."""
        url_unlike = self.url_unlike % (media_id)
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

    # def __init__(self, dic, *args, **kwargs):
    #     dic['owner'] = User(dic['owner'])
    #     super(Media, self).__init__(dic, *args, **kwargs)

    @property
    def url(self):
        return "https://www.instagram.com/p/%s/" % self.code


class User(Base):

    url_user_detail = 'https://www.instagram.com/%s/?__a=1'

    # def __init__(self, dic, *args, **kwargs):
    #     super(User, self).__init__(dic, *args, **kwargs)
