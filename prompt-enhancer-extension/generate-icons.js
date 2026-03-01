#!/usr/bin/env node
// Simple icon generator for Chrome extension
// Generates placeholder icons in PNG format

const fs = require('fs');
const path = require('path');

// Create icons directory
const iconsDir = path.join(__dirname, 'icons');
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir);
}

// Function to generate SVG icon
function generateSVG(size) {
  const svg = `
<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="${size * 0.2}" fill="url(#grad)"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="${size * 0.6}" font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="middle">✨</text>
</svg>`;
  return svg;
}

// Generate icons for different sizes
const sizes = [16, 48, 128];

sizes.forEach(size => {
  const svg = generateSVG(size);
  const svgPath = path.join(iconsDir, `icon${size}.svg`);
  fs.writeFileSync(svgPath, svg);
  console.log(`✓ Generated icon${size}.svg`);
});

console.log('\nIcons generated successfully!');
console.log('\nTo convert SVG to PNG (required for Chrome):');
console.log('Option 1: Use online converter like https://cloudconvert.com/svg-to-png');
console.log('Option 2: Use ImageMagick:');
console.log('  convert icons/icon16.svg icons/icon16.png');
console.log('  convert icons/icon48.svg icons/icon48.png');
console.log('  convert icons/icon128.svg icons/icon128.png');
console.log('\nOption 3: Use this script with canvas:');
console.log('  npm install canvas');
console.log('  node generate-icons.js --convert');

// If --convert flag and canvas is available
if (process.argv.includes('--convert')) {
  try {
    const { createCanvas } = require('canvas');
    
    sizes.forEach(size => {
      const canvas = createCanvas(size, size);
      const ctx = canvas.getContext('2d');
      
      // Create gradient
      const gradient = ctx.createLinearGradient(0, 0, size, size);
      gradient.addColorStop(0, '#667eea');
      gradient.addColorStop(1, '#764ba2');
      
      // Draw rounded rectangle
      const radius = size * 0.2;
      ctx.beginPath();
      ctx.moveTo(radius, 0);
      ctx.lineTo(size - radius, 0);
      ctx.quadraticCurveTo(size, 0, size, radius);
      ctx.lineTo(size, size - radius);
      ctx.quadraticCurveTo(size, size, size - radius, size);
      ctx.lineTo(radius, size);
      ctx.quadraticCurveTo(0, size, 0, size - radius);
      ctx.lineTo(0, radius);
      ctx.quadraticCurveTo(0, 0, radius, 0);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();
      
      // Draw emoji
      ctx.font = `bold ${size * 0.6}px Arial`;
      ctx.fillStyle = 'white';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('✨', size / 2, size / 2);
      
      // Save PNG
      const buffer = canvas.toBuffer('image/png');
      const pngPath = path.join(iconsDir, `icon${size}.png`);
      fs.writeFileSync(pngPath, buffer);
      console.log(`✓ Converted to icon${size}.png`);
    });
    
    console.log('\n✓ All icons converted to PNG format!');
  } catch (err) {
    console.error('\nCanvas module not found. Install with: npm install canvas');
    console.log('Or convert SVG files manually using the methods above.');
  }
}
