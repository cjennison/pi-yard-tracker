import { useEffect, useRef, useState, useCallback } from 'react';
import {
  Stack,
  Title,
  Text,
  Card,
  Group,
  Badge,
  Button,
  Switch,
  NumberInput,
  Paper,
  Alert,
  Center,
  Loader,
  Grid,
  Box,
  Indicator,
  RingProgress,
} from '@mantine/core';
import {
  IconCamera,
  IconCameraOff,
  IconEye,
  IconEyeOff,
  IconInfoCircle,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import dayjs from 'dayjs';

interface Detection {
  id: string;
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
  timestamp: string;
}

interface LiveStats {
  fps: number;
  detection_count: number;
  processing_time: number;
  last_detection: string | null;
  active_classes: string[];
}

export default function LiveView() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showDetections, setShowDetections] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(50);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [recentDetections, setRecentDetections] = useState<Detection[]>([]);
  const [stats, setStats] = useState<LiveStats>({
    fps: 0,
    detection_count: 0,
    processing_time: 0,
    last_detection: null,
    active_classes: [],
  });
  const [error, setError] = useState<string | null>(null);

  // Connect to WebSocket stream
  const connectWebSocket = useCallback(() => {
    setIsLoading(true);
    setError(null);

    try {
      // Connect to the real WebSocket endpoint
      const ws = new WebSocket('ws://localhost:8000/live');
      
      ws.onopen = () => {
        setIsConnected(true);
        setIsLoading(false);
        notifications.show({
          title: 'Live View Connected',
          message: 'Camera feed is now active',
          color: 'green',
          icon: <IconCamera size={16} />,
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'frame') {
            // Update detections
            if (data.detections) {
              const newDetections = data.detections.filter(
                (det: Detection) => det.confidence >= confidenceThreshold / 100
              );
              setDetections(newDetections);
              
              // Add to recent detections (keep last 10)
              setRecentDetections(prev => {
                const updated = [...newDetections, ...prev].slice(0, 10);
                return updated;
              });
            }
            
            // Update stats
            if (data.stats) {
              setStats(data.stats);
            }

            // Update video element with new frame
            if (videoRef.current && data.image) {
              videoRef.current.src = `data:image/jpeg;base64,${data.image}`;
            }
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsLoading(false);
        notifications.show({
          title: 'Live View Disconnected',
          message: 'Camera feed connection lost',
          color: 'orange',
          icon: <IconCameraOff size={16} />,
        });
      };

      ws.onerror = () => {
        setError('Failed to connect to camera feed');
        setIsLoading(false);
        notifications.show({
          title: 'Connection Error',
          message: 'Unable to connect to live camera feed. Make sure the backend is running.',
          color: 'red',
          icon: <IconCameraOff size={16} />,
        });
      };

      wsRef.current = ws;
    } catch (err) {
      setError('WebSocket connection failed');
      setIsLoading(false);
    }
  }, [confidenceThreshold]);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setDetections([]);
    setStats({
      fps: 0,
      detection_count: 0,
      processing_time: 0,
      last_detection: null,
      active_classes: [],
    });
  }, []);

  // Draw detection overlays on canvas
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current || !showDetections) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw detections
    detections.forEach((detection, index) => {
      const bbox = detection.bbox;
      const x = bbox.x_min * canvas.width;
      const y = bbox.y_min * canvas.height;
      const width = bbox.width * canvas.width;
      const height = bbox.height * canvas.height;

      // Get color based on confidence
      const confidence = detection.confidence;
      let color = '#ff6b6b'; // red for low confidence
      if (confidence >= 0.8) color = '#51cf66'; // green for high confidence
      else if (confidence >= 0.6) color = '#ffd43b'; // yellow for medium confidence
      else if (confidence >= 0.4) color = '#ff922b'; // orange for low-medium confidence

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, width, height);

      // Draw confidence indicator
      const confidenceWidth = 60;
      const confidenceHeight = 4;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(x, y - 20, confidenceWidth, confidenceHeight + 12);
      ctx.fillStyle = color;
      ctx.fillRect(x + 2, y - 18, (confidenceWidth - 4) * confidence, confidenceHeight);

      // Draw label if enabled
      if (showLabels) {
        const label = `${detection.class_name} ${(confidence * 100).toFixed(0)}%`;
        ctx.fillStyle = color;
        ctx.font = '14px Arial';
        const textWidth = ctx.measureText(label).width;
        
        // Background for text
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(x, y - 40, textWidth + 8, 18);
        
        // Text
        ctx.fillStyle = 'white';
        ctx.fillText(label, x + 4, y - 26);
      }

      // Animate recent detections with a pulse effect
      if (index < 3) { // Only animate the 3 most recent
        const pulseAlpha = 0.3 + 0.2 * Math.sin(Date.now() * 0.01 + index);
        ctx.fillStyle = `${color}${Math.floor(pulseAlpha * 255).toString(16).padStart(2, '0')}`;
        ctx.fillRect(x, y, width, height);
      }
    });
  }, [detections, showDetections, showLabels]);

  // Update confidence threshold and send to backend
  const updateConfidenceThreshold = useCallback((newThreshold: number) => {
    setConfidenceThreshold(newThreshold);
    
    // Send configuration update to backend
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'config',
        confidence_threshold: newThreshold
      }));
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  return (
    <Stack gap="lg">
      {/* Header */}
      <Group justify="space-between">
        <div>
          <Title order={1} size="h2">Live Camera View</Title>
          <Text c="dimmed" size="sm" mt={4}>
            Real-time wildlife detection with overlay visualization
          </Text>
        </div>
        
        <Group gap="sm">
          <Indicator
            inline
            size={12}
            offset={7}
            position="top-end"
            color={isConnected ? 'green' : 'red'}
            withBorder
          >
            <Button
              variant={isConnected ? 'light' : 'filled'}
              color={isConnected ? 'red' : 'green'}
              loading={isLoading}
              leftSection={isConnected ? <IconCameraOff size={16} /> : <IconCamera size={16} />}
              onClick={isConnected ? disconnectWebSocket : connectWebSocket}
            >
              {isConnected ? 'Stop Feed' : 'Start Feed'}
            </Button>
          </Indicator>
        </Group>
      </Group>

      {error && (
        <Alert icon={<IconInfoCircle size={16} />} title="Connection Error" color="red">
          {error}. Make sure the backend server is running and the camera is connected.
        </Alert>
      )}

      <Grid>
        {/* Live Video Feed */}
        <Grid.Col span={{ base: 12, lg: 8 }}>
          <Card shadow="sm" padding="md" radius="md" withBorder>
            <Stack gap="md">
              <Group justify="space-between">
                <Text fw={600}>Live Camera Feed</Text>
                <Group gap="xs">
                  <Badge
                    variant="dot"
                    color={isConnected ? 'green' : 'gray'}
                    size="sm"
                  >
                    {isConnected ? `${stats.fps.toFixed(1)} FPS` : 'Disconnected'}
                  </Badge>
                  {isConnected && (
                    <Badge variant="light" color="blue" size="sm">
                      {detections.length} active
                    </Badge>
                  )}
                </Group>
              </Group>

              <Box pos="relative" style={{ background: '#000', borderRadius: 8, overflow: 'hidden' }}>
                {!isConnected ? (
                  <Center h={400}>
                    <Stack align="center" gap="md">
                      <IconCamera size={64} color="var(--mantine-color-gray-5)" />
                      <Text c="dimmed" ta="center">
                        {isLoading ? 'Connecting to camera...' : 'Click "Start Feed" to begin live view'}
                      </Text>
                      {isLoading && <Loader size="sm" />}
                    </Stack>
                  </Center>
                ) : (
                  <>
                    <video
                      ref={videoRef}
                      style={{
                        width: '100%',
                        height: '400px',
                        objectFit: 'cover',
                        display: 'block',
                      }}
                      muted
                      playsInline
                    />
                    <canvas
                      ref={canvasRef}
                      width={800}
                      height={400}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        pointerEvents: 'none',
                      }}
                    />
                  </>
                )}
              </Box>

              {/* Controls */}
              <Group justify="space-between">
                <Group gap="md">
                  <Switch
                    label="Show Detections"
                    checked={showDetections}
                    onChange={(e) => setShowDetections(e.currentTarget.checked)}
                    thumbIcon={
                      showDetections ? (
                        <IconEye size={12} color="var(--mantine-color-green-6)" />
                      ) : (
                        <IconEyeOff size={12} color="var(--mantine-color-gray-6)" />
                      )
                    }
                  />
                  <Switch
                    label="Show Labels"
                    checked={showLabels}
                    onChange={(e) => setShowLabels(e.currentTarget.checked)}
                    disabled={!showDetections}
                  />
                </Group>

                <Group gap="md">
                  <NumberInput
                    label="Confidence Threshold"
                    value={confidenceThreshold}
                    onChange={(value) => updateConfidenceThreshold(typeof value === 'number' ? value : 50)}
                    min={0}
                    max={100}
                    step={5}
                    suffix="%"
                    w={120}
                    size="sm"
                  />
                </Group>
              </Group>
            </Stack>
          </Card>
        </Grid.Col>

        {/* Live Statistics & Recent Activity */}
        <Grid.Col span={{ base: 12, lg: 4 }}>
          <Stack gap="md">
            {/* Real-time Stats */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="md">
                <Text fw={600} size="sm">Performance Stats</Text>
                
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">Frame Rate</Text>
                  <Group gap="xs">
                    <Text size="sm" fw={600}>{stats.fps.toFixed(1)} FPS</Text>
                    <RingProgress
                      size={32}
                      thickness={4}
                      sections={[{ value: Math.min(stats.fps * 10, 100), color: stats.fps > 5 ? 'green' : 'orange' }]}
                    />
                  </Group>
                </Group>

                <Group justify="space-between">
                  <Text size="sm" c="dimmed">Processing Time</Text>
                  <Text size="sm" fw={600}>{stats.processing_time.toFixed(0)}ms</Text>
                </Group>

                <Group justify="space-between">
                  <Text size="sm" c="dimmed">Total Detections</Text>
                  <Badge variant="light" color="green">{stats.detection_count}</Badge>
                </Group>

                <Group justify="space-between">
                  <Text size="sm" c="dimmed">Active Classes</Text>
                  <Text size="sm" fw={600}>{stats.active_classes.length}</Text>
                </Group>

                {stats.last_detection && (
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">Last Detection</Text>
                    <Text size="xs">{dayjs(stats.last_detection).fromNow()}</Text>
                  </Group>
                )}
              </Stack>
            </Card>

            {/* Current Detections */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="md">
                <Group justify="space-between">
                  <Text fw={600} size="sm">Current Detections</Text>
                  <Badge variant="light" color="blue" size="sm">
                    {detections.length} active
                  </Badge>
                </Group>

                {detections.length > 0 ? (
                  <Stack gap="sm">
                    {detections
                      .sort((a, b) => b.confidence - a.confidence)
                      .slice(0, 5)
                      .map((detection, index) => (
                        <Paper key={`${detection.id}-${index}`} p="sm" withBorder>
                          <Group justify="space-between">
                            <Group gap="sm">
                              <Badge
                                variant="light"
                                color={detection.confidence >= 0.8 ? 'green' : detection.confidence >= 0.6 ? 'yellow' : 'orange'}
                                size="sm"
                              >
                                {detection.class_name}
                              </Badge>
                              <Text size="sm">{(detection.confidence * 100).toFixed(0)}%</Text>
                            </Group>
                            <Text size="xs" c="dimmed">
                              {Math.round(detection.bbox.width * 100)}×{Math.round(detection.bbox.height * 100)}%
                            </Text>
                          </Group>
                        </Paper>
                      ))}
                  </Stack>
                ) : (
                  <Center py="md">
                    <Text size="sm" c="dimmed">No active detections</Text>
                  </Center>
                )}
              </Stack>
            </Card>

            {/* Recent Activity */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="md">
                <Text fw={600} size="sm">Recent Activity</Text>

                {recentDetections.length > 0 ? (
                  <Stack gap="xs">
                    {recentDetections.slice(0, 8).map((detection, index) => (
                      <Group key={`recent-${detection.id}-${index}`} justify="space-between" wrap="nowrap">
                        <Group gap="xs">
                          <Badge
                            variant="dot"
                            size="xs"
                            color={detection.confidence >= 0.8 ? 'green' : 'orange'}
                          >
                            {detection.class_name}
                          </Badge>
                          <Text size="xs">{(detection.confidence * 100).toFixed(0)}%</Text>
                        </Group>
                        <Text size="xs" c="dimmed">
                          {dayjs(detection.timestamp).format('HH:mm:ss')}
                        </Text>
                      </Group>
                    ))}
                  </Stack>
                ) : (
                  <Center py="md">
                    <Text size="sm" c="dimmed">No recent activity</Text>
                  </Center>
                )}
              </Stack>
            </Card>
          </Stack>
        </Grid.Col>
      </Grid>

      {/* Legend */}
      <Card shadow="sm" padding="md" radius="md" withBorder>
        <Stack gap="sm">
          <Text fw={600} size="sm">Detection Confidence Legend</Text>
          <Group gap="lg">
            <Group gap="xs">
              <div style={{ width: 16, height: 16, backgroundColor: '#51cf66', borderRadius: 2 }} />
              <Text size="sm">High (80%+)</Text>
            </Group>
            <Group gap="xs">
              <div style={{ width: 16, height: 16, backgroundColor: '#ffd43b', borderRadius: 2 }} />
              <Text size="sm">Medium (60-79%)</Text>
            </Group>
            <Group gap="xs">
              <div style={{ width: 16, height: 16, backgroundColor: '#ff922b', borderRadius: 2 }} />
              <Text size="sm">Low-Medium (40-59%)</Text>
            </Group>
            <Group gap="xs">
              <div style={{ width: 16, height: 16, backgroundColor: '#ff6b6b', borderRadius: 2 }} />
              <Text size="sm">Low (Below 40%)</Text>
            </Group>
          </Group>
        </Stack>
      </Card>
    </Stack>
  );
}