__version__ = '1.0'

from kivy.app import App
from kivy.lang import Builder
from gmaps import GMap

gmap_kv = '''
BoxLayout:
    orientation: 'vertical'
    spacing: '4dp'
    padding: '4dp'
    canvas.before:
        Color:
            rgba: 1, 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size

    RelativeLayout:
        GMap:
            id: map_widget

        Button:
            text: 'Should avoid input'
            size_hint: None, None
            size: 200, 200


    Button:
        text: 'Hello World'
        size_hint_y: None
        height: '40dp'
'''

class GMapTestApp(App):

    def build(self):
        self.root = Builder.load_string(gmap_kv)
        self.root.ids.map_widget.bind(on_ready=self.on_map_widget_ready)

    def on_map_widget_ready(self, map_widget, *args):
        # Implementation of the "Hello Map" example from the android
        # documentation
        map = map_widget.map

        sydney = map_widget.create_latlng(-33.867, 151.206)

        #map.setMyLocationEnabled(True)
        #map.moveCamera(map_widget.camera_update_factory.newLatLngZoom(
        #    sydney, 13))

        marker = map_widget.create_marker(
                title='Sydney',
                snippet='The most populous city in Autralia',
                position=sydney)
        map.addMarker(marker)

        # disable zoom button
        map.getUiSettings().setZoomControlsEnabled(False)

    def on_pause(self):
        return True

if __name__ == '__main__':
    GMapTestApp().run()
