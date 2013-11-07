__version__ = '1.3'

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty
from gmaps import GMap, run_on_ui_thread

gmap_kv = '''

<Toolbar@BoxLayout>:
    size_hint_y: None
    height: '48dp'
    padding: '4dp'
    spacing: '4dp'

    canvas:
        Color:
            rgba: .2, .2, .2, .6
        Rectangle:
            pos: self.pos
            size: self.size


FloatLayout:
    GMap:
        id: map_widget

    # top toolbar
    Toolbar:
        pos_hint: {'top': 1}
        Button:
            text: 'Move to Lille, France'
            on_release: app.move_to_lille()

        Button:
            text: 'Move to Sydney, Autralia'
            on_release: app.move_to_sydney()

    # bottom toolbar
    Toolbar:
        Label:
            text: 'Longitude: {} - Latitude: {}'.format(app.longitude, app.latitude)
'''

class GMapTestApp(App):

    latitude = NumericProperty()
    longitude = NumericProperty()

    def build(self):
        self.root = Builder.load_string(gmap_kv)
        self.map_widget = self.root.ids.map_widget
        self.map_widget.bind(
                on_ready=self.on_map_widget_ready,
                on_map_click=self.on_map_click)

    def on_map_widget_ready(self, map_widget, *args):
        # Implementation of the "Hello Map" example from the android
        # documentation
        map = map_widget.map

        sydney = map_widget.create_latlng(-33.867, 151.206)

        #map.setMyLocationEnabled(True)
        map.moveCamera(map_widget.camera_update_factory.newLatLngZoom(
            sydney, 13))

        marker = map_widget.create_marker(
                title='Sydney',
                snippet='The most populous city in Autralia',
                position=sydney)
        map.addMarker(marker)

        # disable zoom button
        map.getUiSettings().setZoomControlsEnabled(False)

    @run_on_ui_thread
    def move_to_lille(self):
        latlng = self.map_widget.create_latlng(50.6294, 3.057)
        self.map_widget.map.moveCamera(
            self.map_widget.camera_update_factory.newLatLngZoom(
                latlng, 13))

    @run_on_ui_thread
    def move_to_sydney(self):
        latlng = self.map_widget.create_latlng(-33.867, 151.206)
        self.map_widget.map.moveCamera(
            self.map_widget.camera_update_factory.newLatLngZoom(
                latlng, 13))

    def on_map_click(self, map_widget, latlng):
        self.latitude = latlng.latitude
        self.longitude = latlng.longitude

    def on_pause(self):
        return True


if __name__ == '__main__':
    GMapTestApp().run()
