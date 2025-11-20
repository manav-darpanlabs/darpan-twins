import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface AnimatedGradientBackgroundProps {
  startingGap?: number;
  breathing?: boolean;
  gradientColors?: string[];
  gradientStops?: number[];
  animationSpeed?: number;
  breathingRange?: number;
  containerStyle?: React.CSSProperties;
  containerClassName?: string;
  topOffset?: number;
}

const AnimatedGradientBackground: React.FC<AnimatedGradientBackgroundProps> = ({
  startingGap = 120,
  breathing = true,
  gradientColors = [
    "#020617",   // Deep near-black base
    "#00F5A0",   // Neon green (Darpan signature)
    "#00D9F5",   // Neon cyan
    "#38BDF8",   // Bright blue
    "#22C55E",   // Vivid green
    "#A855F7",   // Purple accent
    "#0EA5E9"    // Electric blue
  ],
  gradientStops = [25, 45, 60, 72, 82, 92, 100],
  animationSpeed = 0.003,
  breathingRange = 20,
  containerStyle = {},
  containerClassName = '',
  topOffset = 0,
}) => {
  const animationRef = useRef<number | null>(null);
  const widthRef = useRef(startingGap);
  const directionRef = useRef(1);

  // Validate gradient arrays match in length
  if (gradientColors.length !== gradientStops.length) {
    throw new Error(
      `AnimatedGradientBackground: gradientColors (${gradientColors.length}) and gradientStops (${gradientStops.length}) must have the same length`
    );
  }

  // Build the radial gradient string
  const buildGradientString = (width: number): string => {
    const gradientPairs = gradientColors
      .map((color, index) => `${color} ${gradientStops[index]}%`)
      .join(', ');
    return `radial-gradient(${width}% ${width}% at 50% 50%, ${gradientPairs})`;
  };

  useEffect(() => {
    if (!breathing) return;

    const animate = () => {
      // Update width with breathing effect
      widthRef.current += directionRef.current * animationSpeed * breathingRange;

      // Reverse direction at boundaries
      if (widthRef.current >= startingGap + breathingRange) {
        widthRef.current = startingGap + breathingRange;
        directionRef.current = -1;
      } else if (widthRef.current <= startingGap - breathingRange) {
        widthRef.current = startingGap - breathingRange;
        directionRef.current = 1;
      }

      // Apply the gradient
      const element = document.getElementById('animated-gradient-bg');
      if (element) {
        element.style.background = buildGradientString(widthRef.current);
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    // Start animation
    animationRef.current = requestAnimationFrame(animate);

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [breathing, startingGap, breathingRange, animationSpeed, gradientColors, gradientStops]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 1.2,
        ease: [0.22, 0.61, 0.36, 1], // Smooth easing curve
      }}
      className={`absolute inset-0 overflow-hidden ${containerClassName}`}
      style={{
        top: topOffset,
        ...containerStyle,
      }}
    >
      <div
        id="animated-gradient-bg"
        className="absolute inset-0 w-full h-full"
        style={{
          background: buildGradientString(startingGap),
          filter: 'blur(80px)', // Soft gradient blur
        }}
      />

      {/* Noise texture overlay for depth */}
      <div
        className="absolute inset-0 opacity-[0.015] mix-blend-screen"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '128px 128px',
        }}
      />

      {/* Grid overlay for lab aesthetic */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 245, 160, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 217, 245, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
        }}
      />
    </motion.div>
  );
};

export default AnimatedGradientBackground;
