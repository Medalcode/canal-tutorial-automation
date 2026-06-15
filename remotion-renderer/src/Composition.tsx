import React from 'react';
import { AbsoluteFill, Sequence, Audio, staticFile, useVideoConfig, useCurrentFrame } from 'remotion';
import { Avatar } from './Avatar';
import { CodeEditor } from './CodeEditor';

type Scene = {
  id: string;
  duration: number;
  commands?: string[];
  language?: string;
};

type Subtitle = {
  text: string;
  start: number;
  end: number;
};

export const TutorialComposition: React.FC<{ audio_duration: number; scenes: Scene[]; subtitles?: Subtitle[] }> = ({
  audio_duration,
  scenes,
  subtitles = []
}) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  let currentTime = 0;
  // Intro duration
  const introDuration = 6 * fps;
  currentTime += introDuration;
  
  const currentAudioTime = (frame - introDuration) / fps;
  const activeSubtitle = subtitles.find(s => currentAudioTime >= s.start && currentAudioTime <= s.end);

  return (
    <AbsoluteFill style={{ backgroundColor: '#1e1e1e' }}>
      {/* El audio empieza justo despues de la intro */}
      <Sequence from={introDuration}>
         <Audio src={staticFile('narracion.mp3')} />
      </Sequence>
      
      {/* Secuencia Intro */}
      <Sequence from={0} durationInFrames={introDuration}>
         <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', color: 'white', fontSize: 80, backgroundColor: '#007acc' }}>
             Canal Tutorial Automation 2.0
         </AbsoluteFill>
      </Sequence>

      {/* Escenas Principales */}
      {scenes.map((scene) => {
        const sceneFrames = Math.round(scene.duration * fps);
        const seq = (
          <Sequence key={scene.id} from={currentTime} durationInFrames={sceneFrames}>
            <AbsoluteFill style={{ flexDirection: 'row' }}>
              <Avatar />
              <div style={{ flex: '0 0 60%', height: '100%', position: 'relative' }}>
                <CodeEditor 
                  code={(scene.commands || []).join('\\n')} 
                  charsPerSecond={15} 
                  language={scene.language || 'python'} 
                />
              </div>
            </AbsoluteFill>
          </Sequence>
        );
        currentTime += sceneFrames;
        return seq;
      })}

      {/* Secuencia Outro */}
      <Sequence from={currentTime} durationInFrames={8 * fps}>
         <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', color: 'white', fontSize: 80, backgroundColor: 'black' }}>
             Gracias por ver. ¡Suscríbete!
         </AbsoluteFill>
      </Sequence>

      {/* Subtitulos superpuestos confinándolos a la columna del Avatar (40%) */}
      {frame >= introDuration && frame < currentTime && activeSubtitle && (
        <AbsoluteFill style={{ 
          width: '40%', 
          left: 0, 
          justifyContent: 'flex-end', 
          alignItems: 'center', 
          paddingBottom: 60,
          paddingLeft: 20,
          paddingRight: 20
        }}>
          <div style={{
             backgroundColor: 'rgba(0,0,0,0.85)',
             color: '#eab308', // Yellow 500
             padding: '15px 30px',
             borderRadius: 16,
             fontSize: 48, // Letra más pequeña para que quepa bien en el 40%
             fontWeight: 'bold',
             fontFamily: 'Inter, sans-serif',
             border: '3px solid #3b82f6', // Border blue
             textAlign: 'center',
             boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
          }}>
            {activeSubtitle.text}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
