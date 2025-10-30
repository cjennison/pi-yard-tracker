import { useEffect, useRef, useState } from "react";
import { Box, Loader, Center } from "@mantine/core";

interface Detection {
  id: number;
  class_name: string;
  confidence: number;
  bbox: {
    x_min: number;
    y_min: number;
    x_max: number;
    y_max: number;
    x_center: number;
    y_center: number;
    width: number;
    height: number;
  };
}

interface ImageWithDetectionsProps {
  src: string;
  alt: string;
  detections?: Detection[];
  maxHeight?: number;
  showLabels?: boolean;
}

export default function ImageWithDetections({
  src,
  detections = [],
  maxHeight = 500,
  showLabels = true,
}: ImageWithDetectionsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new window.Image();
    img.crossOrigin = "anonymous";

    img.onload = () => {
      // Calculate scaled dimensions while maintaining aspect ratio
      let drawWidth = img.width;
      let drawHeight = img.height;

      if (drawHeight > maxHeight) {
        const scale = maxHeight / drawHeight;
        drawWidth = img.width * scale;
        drawHeight = maxHeight;
      }

      // Set canvas size
      canvas.width = drawWidth;
      canvas.height = drawHeight;

      // Draw image
      ctx.drawImage(img, 0, 0, drawWidth, drawHeight);

      // Draw bounding boxes
      if (detections && detections.length > 0) {
        detections.forEach((detection) => {
          const bbox = detection.bbox;

          // Convert normalized coordinates to pixel coordinates
          const x = bbox.x_min * drawWidth;
          const y = bbox.y_min * drawHeight;
          const width = bbox.width * drawWidth;
          const height = bbox.height * drawHeight;

          // Draw bounding box
          ctx.strokeStyle = "#3b82f6"; // Blue color
          ctx.lineWidth = 3;
          ctx.strokeRect(x, y, width, height);

          // Draw label background and text if enabled
          if (showLabels) {
            const label = `${detection.class_name} ${(
              detection.confidence * 100
            ).toFixed(1)}%`;
            ctx.font = "bold 14px sans-serif";
            const textMetrics = ctx.measureText(label);
            const textWidth = textMetrics.width;
            const textHeight = 20;

            // Draw label background
            ctx.fillStyle = "#3b82f6";
            ctx.fillRect(x, y - textHeight - 4, textWidth + 10, textHeight + 4);

            // Draw label text
            ctx.fillStyle = "#ffffff";
            ctx.fillText(label, x + 5, y - 8);
          }
        });
      }

      setImageLoaded(true);
      setIsLoading(false);
    };

    img.onerror = () => {
      setIsLoading(false);
    };

    img.src = src;
  }, [src, detections, maxHeight, showLabels]);

  return (
    <Box pos="relative">
      {isLoading && (
        <Center h={maxHeight}>
          <Loader size="lg" />
        </Center>
      )}
      <canvas
        ref={canvasRef}
        style={{
          display: imageLoaded ? "block" : "none",
          maxWidth: "100%",
          height: "auto",
        }}
      />
    </Box>
  );
}
