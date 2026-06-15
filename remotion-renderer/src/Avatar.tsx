import React from 'react';
import { useCurrentFrame, useVideoConfig, Img, staticFile } from 'remotion';
import { useAudioData, visualizeAudio } from '@remotion/media-utils';

export const Avatar: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Audio data for reactivity
  const audioData = useAudioData(staticFile('narracion.mp3'));
  
  let mouthScale = 1;
  let bounce = Math.abs(Math.sin(frame / 10)) * 5; // Idle bounce

  if (audioData) {
    // Calculamos el volumen en este frame. Intro dura 6s.
    const introFrames = 6 * fps;
    const audioFrame = frame - introFrames;
    if (audioFrame >= 0) {
      const visualization = visualizeAudio({
        fps,
        frame: audioFrame,
        audioData,
        numberOfSamples: 16,
      });
      
      // Suma de frecuencias para detectar volumen general
      const volume = visualization.reduce((a, b) => a + b, 0) / visualization.length;
      
      // Escalar la boca en base al volumen
      mouthScale = 1 + volume * 1.5; // Multiplicador de reaccion
      bounce += volume * 10; // Rebote extra al hablar fuerte
    }
  }

  return (
    <div style={{
      flex: '0 0 40%',
      height: '100%',
      backgroundColor: '#18181b', // Zinc 900
      display: 'flex', 
      flexDirection: 'column',
      justifyContent: 'center', 
      alignItems: 'center', 
      borderRight: '4px solid #3b82f6', // Blue 500
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Fondo decorativo (grid) */}
      <div style={{
         position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
         backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)',
         backgroundSize: '40px 40px',
         opacity: 0.2
      }} />

      <div style={{
        width: 320,
        height: 320,
        backgroundColor: '#27272a', // Zinc 800
        borderRadius: '50%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        transform: `translateY(-${bounce}px) scale(${mouthScale > 1.05 ? 1.02 : 1})`,
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(59, 130, 246, 0.3)',
        border: '6px solid #3b82f6',
        zIndex: 10,
        overflow: 'hidden'
      }}>
        {/* Avatar image */}
        <Img 
          src={staticFile("avatar.png")} 
          style={{ 
            width: '100%', 
            height: '100%', 
            objectFit: 'cover' 
          }} 
        />
      </div>
      
      <div style={{
        marginTop: 50,
        background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
        color: 'white',
        padding: '15px 40px',
        borderRadius: 30,
        fontFamily: 'Inter, sans-serif',
        fontWeight: 'bold',
        fontSize: 32,
        letterSpacing: '1px',
        boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.5)',
        zIndex: 10,
        transform: `translateY(-${bounce * 0.5}px)`
      }}>
        Experto IA
      </div>
    </div>
  );
};
