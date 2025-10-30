import { Center, Loader, Stack, Text, Progress, Box } from "@mantine/core";
import { IconCamera, IconEye, IconPhoto } from "@tabler/icons-react";

interface LoadingProps {
  size?: "sm" | "md" | "lg" | "xl";
  text?: string;
  type?: "default" | "photos" | "detections" | "camera";
  progress?: number;
  showProgress?: boolean;
}

const loadingIcons = {
  default: IconEye,
  photos: IconPhoto,
  detections: IconEye,
  camera: IconCamera,
};

const loadingTexts = {
  default: "Loading...",
  photos: "Loading photos...",
  detections: "Loading detections...",
  camera: "Connecting to camera...",
};

export default function Loading({
  size = "md",
  text,
  type = "default",
  progress,
  showProgress = false,
}: LoadingProps) {
  const Icon = loadingIcons[type];
  const defaultText = text || loadingTexts[type];

  return (
    <Center py="xl">
      <Stack align="center" gap="lg">
        <Box pos="relative">
          <Loader size={size === "sm" ? "md" : size === "lg" ? "xl" : "lg"} />
          <Icon
            size={size === "sm" ? 20 : size === "lg" ? 32 : 24}
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              color: "var(--mantine-color-blue-6)",
              opacity: 0.7,
            }}
          />
        </Box>

        <Stack align="center" gap="xs">
          <Text size={size === "sm" ? "sm" : "md"} fw={500} c="dimmed">
            {defaultText}
          </Text>

          {showProgress && progress !== undefined && (
            <Box w={200}>
              <Progress
                value={progress}
                size="sm"
                radius="xl"
                animated
                color="blue"
              />
              <Text size="xs" c="dimmed" ta="center" mt={4}>
                {Math.round(progress)}% complete
              </Text>
            </Box>
          )}
        </Stack>
      </Stack>
    </Center>
  );
}

// Skeleton loader for cards
export function CardSkeleton({ height = 200 }: { height?: number }) {
  return (
    <Box>
      <div
        style={{
          height,
          background:
            "linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)",
          backgroundSize: "200px 100%",
          animation: "shimmer 1.5s infinite",
          borderRadius: "var(--mantine-radius-md)",
        }}
      />
    </Box>
  );
}

// Pulse loading animation
export function PulseLoader({
  size = 40,
  color = "blue",
}: {
  size?: number;
  color?: string;
}) {
  return (
    <Box
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        backgroundColor: `var(--mantine-color-${color}-6)`,
        animation: "pulse 1.5s ease-in-out infinite",
      }}
    />
  );
}
