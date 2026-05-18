import React, { useState, useEffect } from 'react'
import { speakText } from '../../api'
import './WelcomeSplash.css'

export default function WelcomeSplash({ onEnter }) {
  const [isEntering, setIsEntering] = useState(false)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)

  const handleStart = async () => {
    if (isEntering) return
    setIsEntering(true)
    setIsPlayingAudio(true)

    // A beautiful, highly emotional welcoming line for Indian farmers
    const welcomeText = "नमस्ते किसान भाई! किसानवाणी में आपका स्वागत है। देश के अन्नदाता, हमारी शान, आपके हर सवाल का जवाब अब आपकी अपनी आवाज़ में। चलिए मिलकर कृषि का नया अध्याय लिखते हैं!"

    try {
      // Dynamically generate the welcome audio via our Sarvam AI TTS endpoint!
      const audioUrl = await speakText(welcomeText, 'hi-IN')
      const audio = new Audio(audioUrl)
      
      audio.onended = () => {
        setIsPlayingAudio(false)
        URL.revokeObjectURL(audioUrl)
        onEnter() // Fade out splash screen after audio finishes or is well into play
      }

      audio.onerror = () => {
        console.warn('[Splash] Audio play failed, transitioning immediately')
        URL.revokeObjectURL(audioUrl)
        onEnter()
      }

      await audio.play()
      
      // We start fading out the overlay 2 seconds into the gorgeous voice to make the transition super slick!
      setTimeout(() => {
        onEnter()
      }, 3500)

    } catch (err) {
      console.warn('[Splash] Voice generation failed, skipping audio:', err)
      onEnter()
    }
  }

  return (
    <div className={`welcome-splash-overlay ${isEntering ? 'fade-out' : ''}`}>
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
          <p className="dedication-text">
            "देश के अन्नदाताओं को समर्पित एक डिजिटल आवाज़, जो वैज्ञानिक कृषि और समृद्धि के नए द्वार खोलेगी।"
          </p>
        </div>

        <button 
          className={`enter-btn ${isEntering ? 'entering' : ''}`}
          onClick={handleStart}
          disabled={isEntering}
        >
          {isEntering ? (
            <span className="btn-spinner">🌽 स्वागत हो रहा है...</span>
          ) : (
            <span className="btn-content">🚜 प्रवेश करें / Enter Portal</span>
          )}
        </button>
      </div>
    </div>
  )
}
