import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { useCurrentFrame, useVideoConfig, delayRender, continueRender } from 'remotion';

export const CodeEditor: React.FC<{ code: string; charsPerSecond: number; language?: string }> = ({ 
  code, 
  charsPerSecond,
  language = "python"
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [handle] = useState(() => delayRender("Loading Monaco Editor"));

  // Calculate typed code
  const time = frame / fps;
  const numChars = Math.floor(time * charsPerSecond);
  const currentCode = code.slice(0, numChars);

  return (
    <div style={{ flex: 1, height: '100%', backgroundColor: '#1e1e1e', padding: '20px' }}>
      <Editor
        height="100%"
        defaultLanguage={language}
        theme="vs-dark"
        value={currentCode}
        options={{
          minimap: { enabled: false },
          fontSize: 28,
          lineHeight: 40,
          readOnly: true,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          scrollbar: {
            vertical: 'hidden',
            horizontal: 'hidden'
          }
        }}
        onMount={() => continueRender(handle)}
      />
    </div>
  );
};
