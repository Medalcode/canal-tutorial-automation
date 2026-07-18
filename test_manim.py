from manim import WHITE, Scene, Text, Write


class SceneAnim(Scene):
    def construct(self):
        t = Text("Prueba", color=WHITE)
        self.play(Write(t))
        self.wait(1)
