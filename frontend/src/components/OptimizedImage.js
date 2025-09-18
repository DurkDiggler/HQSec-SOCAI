import React, { useState, useRef, useEffect } from 'react';
import { LazyImage } from '../utils/lazyLoading';

/**
 * Optimized image component with compression, lazy loading, and responsive sizing
 */
const OptimizedImage = ({
  src,
  alt,
  width,
  height,
  quality = 80,
  format = 'webp',
  placeholder = true,
  className = '',
  style = {},
  onLoad,
  onError,
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(null);
  const imgRef = useRef();

  // Generate optimized image URL
  const getOptimizedSrc = (originalSrc, width, height, quality, format) => {
    if (!originalSrc) return originalSrc;
    
    // If it's a data URL or external URL, return as is
    if (originalSrc.startsWith('data:') || originalSrc.startsWith('http')) {
      return originalSrc;
    }

    // For local images, we can add optimization parameters
    const params = new URLSearchParams();
    if (width) params.append('w', width);
    if (height) params.append('h', height);
    if (quality) params.append('q', quality);
    if (format) params.append('f', format);
    
    const queryString = params.toString();
    return queryString ? `${originalSrc}?${queryString}` : originalSrc;
  };

  // Generate responsive srcset
  const generateSrcSet = (originalSrc, baseWidth, baseHeight) => {
    if (!originalSrc || originalSrc.startsWith('data:')) return null;
    
    const sizes = [320, 640, 768, 1024, 1280, 1920];
    const srcSet = sizes
      .filter(size => size <= baseWidth * 2) // Don't upscale
      .map(size => {
        const optimizedSrc = getOptimizedSrc(originalSrc, size, Math.round((size * baseHeight) / baseWidth), quality, format);
        return `${optimizedSrc} ${size}w`;
      })
      .join(', ');
    
    return srcSet || null;
  };

  useEffect(() => {
    if (src) {
      const optimizedSrc = getOptimizedSrc(src, width, height, quality, format);
      setCurrentSrc(optimizedSrc);
    }
  }, [src, width, height, quality, format]);

  const handleLoad = (e) => {
    setIsLoaded(true);
    setHasError(false);
    onLoad && onLoad(e);
  };

  const handleError = (e) => {
    setHasError(true);
    setIsLoaded(false);
    onError && onError(e);
  };

  const placeholderStyle = {
    backgroundColor: '#f0f0f0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: height || '200px',
    minWidth: width || '200px',
    ...style,
  };

  const imageStyle = {
    width: width || '100%',
    height: height || 'auto',
    objectFit: 'cover',
    transition: 'opacity 0.3s ease-in-out',
    opacity: isLoaded ? 1 : 0,
    ...style,
  };

  if (hasError) {
    return (
      <div className={`optimized-image-error ${className}`} style={placeholderStyle}>
        <div style={{ textAlign: 'center', color: '#666' }}>
          <div>📷</div>
          <div>Image failed to load</div>
        </div>
      </div>
    );
  }

  if (!currentSrc) {
    return (
      <div className={`optimized-image-placeholder ${className}`} style={placeholderStyle}>
        <div style={{ textAlign: 'center', color: '#999' }}>
          <div>⏳</div>
          <div>Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`optimized-image-container ${className}`} style={{ position: 'relative' }}>
      {placeholder && !isLoaded && (
        <div className="optimized-image-placeholder" style={placeholderStyle}>
          <div style={{ textAlign: 'center', color: '#999' }}>
            <div>⏳</div>
            <div>Loading...</div>
          </div>
        </div>
      )}
      
      <LazyImage
        src={currentSrc}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        style={imageStyle}
        ref={imgRef}
        {...props}
      />
      
      {currentSrc && (
        <img
          src={currentSrc}
          alt={alt}
          width={width}
          height={height}
          srcSet={generateSrcSet(src, width, height)}
          sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
          onLoad={handleLoad}
          onError={handleError}
          style={{
            ...imageStyle,
            position: isLoaded ? 'static' : 'absolute',
            top: 0,
            left: 0,
            opacity: isLoaded ? 1 : 0,
            visibility: isLoaded ? 'visible' : 'hidden',
          }}
          loading="lazy"
          decoding="async"
        />
      )}
    </div>
  );
};

/**
 * Image gallery component with optimized loading
 */
export const OptimizedImageGallery = ({ images, columns = 3, gap = '16px' }) => {
  const [loadedImages, setLoadedImages] = useState(new Set());

  const handleImageLoad = (index) => {
    setLoadedImages(prev => new Set([...prev, index]));
  };

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap,
    width: '100%',
  };

  return (
    <div className="optimized-image-gallery" style={gridStyle}>
      {images.map((image, index) => (
        <OptimizedImage
          key={index}
          src={image.src}
          alt={image.alt || `Gallery image ${index + 1}`}
          width={image.width}
          height={image.height}
          onLoad={() => handleImageLoad(index)}
          style={{
            width: '100%',
            height: '200px',
            objectFit: 'cover',
            borderRadius: '8px',
          }}
        />
      ))}
    </div>
  );
};

/**
 * Avatar component with fallback
 */
export const OptimizedAvatar = ({ src, alt, size = 40, fallback, ...props }) => {
  const [hasError, setHasError] = useState(false);

  const avatarStyle = {
    width: size,
    height: size,
    borderRadius: '50%',
    objectFit: 'cover',
    backgroundColor: '#e0e0e0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: size * 0.4,
    fontWeight: 'bold',
    color: '#666',
  };

  if (hasError || !src) {
    return (
      <div style={avatarStyle} {...props}>
        {fallback || alt?.charAt(0)?.toUpperCase() || '?'}
      </div>
    );
  }

  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      style={avatarStyle}
      onError={() => setHasError(true)}
      {...props}
    />
  );
};

export default OptimizedImage;
