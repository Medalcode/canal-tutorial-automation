from manim import *
class SceneAnim(Scene):
    def construct(self):
        t = Text("Prueba", color=WHITE)
        self.play(Write(t))
        self.wait(1)
