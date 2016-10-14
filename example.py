#!coding:utf-8

from pygram.api import PyGram


api = PyGram('user', 'password')

for media in api.get_medias_to_collect_by_tag('wedding'):
    print api.like(media)
    print api.follow(media.owner)
    print api.unlike(media)

api.logout()
