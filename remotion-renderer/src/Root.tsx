import "./index.css";
import { Composition, getInputProps } from "remotion";
import { TutorialComposition } from "./Composition";

const defaultProps = {
  audio_duration: 10,
  scenes: [
    {
      id: "test",
      duration: 10,
      commands: ["def saludar():\\n    print('¡Hola Remotion!')\\n\\nif __name__ == '__main__':\\n    saludar()"],
      language: "python"
    }
  ]
};

const inputProps = getInputProps() || {};
// Remotion a veces pasa un objeto vacío, asi que hacemos un merge seguro
const finalProps = inputProps.scenes ? (inputProps as any) : defaultProps;

export const RemotionRoot: React.FC = () => {
  const fps = 30;
  const introFrames = 6 * fps;
  const outroFrames = 8 * fps;
  const scenesFrames = finalProps.scenes.reduce((acc: number, s: any) => acc + Math.round(s.duration * fps), 0);
  const totalFrames = introFrames + scenesFrames + outroFrames;

  return (
    <>
      <Composition
        id="Tutorial"
        component={TutorialComposition}
        durationInFrames={totalFrames}
        fps={fps}
        width={1920}
        height={1080}
        defaultProps={finalProps}
      />
    </>
  );
};
