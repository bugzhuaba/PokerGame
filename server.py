import socket
import qrcode
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color

class PokerServerApp(App):
    def build(self):
        self.title = 'Texas Hold\'em'
        layout =FloatLayout()
        bg = Image(source='picture/table.png', allow_stretch=True, keep_ratio=False)
        layout.add_widget(bg)
        top = FloatLayout()
        title = Image(source='picture/title.png', size_hint=(0.4,0.2), pos_hint = {'center_x': 0.5, 'center_y': 0.65})
        top.add_widget(title)
        layout.add_widget(top)
        rule_bt = Button(text='RULE', size_hint=(0.1, 0.05), pos_hint = {'center_x': 0.4, 'center_y': 0.44},background_color=(1, 0, 0, 1) )
        rule_bt.bind(on_press=self.show_rule)
        top.add_widget(rule_bt)
        start_bt = Button(text='START', size_hint=(0.1, 0.05), pos_hint={'center_x': 0.6, 'center_y': 0.44},background_color=(1, 0, 0, 1))
        top.add_widget(start_bt)
        return layout

    def show_rule(self, instance):
        popup = Popup(title = 'RULE', size_hint = (0.6, 0.6),background='picture/blackboard.png')
        rule_label = Label(text = 'test'+ '\n' +'test')
        popup.content = rule_label
        popup.open()


if __name__ == '__main__':
    PokerServerApp().run()
