import React, { useEffect, useState } from 'react'
import { speakText } from '../../api'
import './WelcomeSplash.css'

export default function WelcomeSplash({ onEnter }) {
  const [welcomeAudio, setWelcomeAudio] = useState(null)

  useEffect(() => {
    // 1. A beautiful, highly emotional welcoming line for Indian farmers
    const welcomeText = "नमस्ते किसान भाई! किसानवाणी में आपका स्वागत है। देश के अन्नदाता, हमारी शान, आपके हर सवाल का जवाब अब आपकी अपनी आवाज़ में। चलिए मिलकर कृषि का नया अध्याय लिखते हैं!"
    let activeAudio = null
    let audioUrl = ""

    // 2. We request the welcoming audio and attempt to play it automatically
    speakText(welcomeText, 'hi-IN').then(url => {
      audioUrl = url
      activeAudio = new Audio(url)
      setWelcomeAudio(activeAudio)

      // Try autoplaying the welcome voice.
      // If the browser blocks autoplay without click, it will fail silently in catch()
      // but the logo animation will still play beautifully for the duration of the splash!
      activeAudio.play()
        .then(() => {
          console.log('[Splash] Welcome voice playing successfully')
        })
        .catch(err => {
          console.warn('[Splash] Autoplay blocked by browser policy, continuing visually:', err)
        })
    }).catch(err => {
      console.warn('[Splash] Voice generation failed:', err)
    })

    // 3. Automatic transition after 4.2 seconds (allowing the stunning logo animation to shine)
    const transitionTimer = setTimeout(() => {
      // Clean up audio references
      if (activeAudio) {
        try { activeAudio.pause() } catch (e) {}
      }
      if (audioUrl) {
        try { URL.revokeObjectURL(audioUrl) } catch (e) {}
      }
      onEnter()
    }, 4200)

    // Cleanup on unmount
    return () => {
      clearTimeout(transitionTimer)
      if (activeAudio) {
        try { activeAudio.pause() } catch (e) {}
      }
      if (audioUrl) {
        try { URL.revokeObjectURL(audioUrl) } catch (e) {}
      }
    }
  }, [onEnter])

  return (
    <div className="welcome-splash-overlay">
      <div className="welcome-splash-container">
        {/* Animated glowing video-style golden logo */}
        <div className="logo-animation-wrapper">
          <div className="logo-ring ring-1"></div>
          <div className="logo-ring ring-2"></div>
          <div className="logo-ring ring-3"></div>
          <div className="glowing-logo-core">
            <span className="logo-emoji">🌾</span>
          </div>
        </div>

        <h1 className="splash-title">KisaanVaani</h1>
        <p className="splash-subtitle">हर किसान की आवाज़, हर सवाल का जवाब</p>
        
        <div className="dedication-card">
          <h2 className="motto-text">🇮🇳 जय जवान, जय किसान, जय विज्ञान! 🌾</h2>
          <p className="dedication-text">
            "देश के अन्नदाताओं को समर्पित एक डिजिटल आवाज़, जो वैज्ञानिक कृषि और समृद्धि के नए द्वार खोलेगी।"
          </p>
        </div>

        <div className="splash-loading-indicator">
          <span className="sparkle-grain">🌾</span>
          <span className="indicator-label">लोड हो रहा है... / Connecting...</span>
        </div>
      </div>
    </div>
  )
}
