import { useState } from "react";
import {
  Stack,
  Title,
  Text,
  Grid,
  Card,
  Image,
  Group,
  Badge,
  Button,
  Modal,
  Pagination,
  TextInput,
  Select,
  Switch,
  ActionIcon,
  Box,
  Paper,
  Skeleton,
  Alert,
  Center,
  Loader,
  Tooltip,
  NumberInput,
} from "@mantine/core";
import {
  IconSearch,
  IconFilter,
  IconX,
  IconEye,
  IconCamera,
  IconZoomIn,
  IconDownload,
  IconClock,
  IconPhoto,
  IconInfoCircle,
} from "@tabler/icons-react";
import { useDisclosure } from "@mantine/hooks";
import { usePhotos, usePhoto } from "../../api/hooks";
import dayjs from "dayjs";

export default function Photos() {
  const [page, setPage] = useState(1);
  const [hasDetectionsOnly, setHasDetectionsOnly] = useState(false);
  const [minDetections, setMinDetections] = useState<number | string>("");
  const [sortBy, setSortBy] = useState<string>("timestamp");
  const [search, setSearch] = useState("");
  const [selectedPhotoId, setSelectedPhotoId] = useState<number | null>(null);
  const [modalOpened, { open: openModal, close: closeModal }] =
    useDisclosure(false);

  const PAGE_SIZE = 20;

  // Fetch photos with current filters
  const {
    data: photosData,
    isLoading: photosLoading,
    error: photosError,
  } = usePhotos({
    page,
    limit: PAGE_SIZE,
    has_detections: hasDetectionsOnly || undefined,
    min_detections:
      typeof minDetections === "number" ? minDetections : undefined,
  });

  // Fetch selected photo details
  const { data: selectedPhoto, isLoading: photoLoading } =
    usePhoto(selectedPhotoId);

  const handlePhotoClick = (photoId: number) => {
    setSelectedPhotoId(photoId);
    openModal();
  };

  const handleModalClose = () => {
    closeModal();
    setSelectedPhotoId(null);
  };

  const filteredPhotos = photosData?.photos.filter((photo) => {
    if (
      search &&
      !photo.filename.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const totalPages = photosData ? Math.ceil(photosData.total / PAGE_SIZE) : 0;

  const getImageUrl = (filepath: string) => {
    // Assuming the backend serves images at /photos/image/{filename}
    const filename = filepath.split("/").pop();
    return `http://localhost:8000/photos/image/${filename}`;
  };

  if (photosError) {
    return (
      <Alert
        icon={<IconInfoCircle size={16} />}
        title="Connection Error"
        color="red"
      >
        Unable to load photos. Please ensure the backend server is running.
      </Alert>
    );
  }

  return (
    <Stack gap="lg">
      {/* Header */}
      <div>
        <Title order={1} size="h2">
          Photo Gallery
        </Title>
        <Text c="dimmed" size="sm" mt={4}>
          Browse all captured photos with wildlife detections
        </Text>
      </div>

      {/* Filters */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group justify="space-between">
            <Text fw={600} size="sm">
              Filters
            </Text>
            <Group gap="xs">
              <Button
                variant="light"
                size="xs"
                leftSection={<IconX size={14} />}
                onClick={() => {
                  setSearch("");
                  setHasDetectionsOnly(false);
                  setMinDetections("");
                  setSortBy("timestamp");
                  setPage(1);
                }}
              >
                Clear All
              </Button>
            </Group>
          </Group>

          <Grid>
            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <TextInput
                placeholder="Search by filename..."
                leftSection={<IconSearch size={16} />}
                value={search}
                onChange={(e) => setSearch(e.currentTarget.value)}
              />
            </Grid.Col>

            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <Select
                placeholder="Sort by"
                data={[
                  { value: "timestamp", label: "Date (Newest)" },
                  { value: "timestamp_asc", label: "Date (Oldest)" },
                  { value: "detection_count", label: "Most Detections" },
                  { value: "filename", label: "Filename" },
                ]}
                value={sortBy}
                onChange={(value) => setSortBy(value || "timestamp")}
              />
            </Grid.Col>

            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <NumberInput
                placeholder="Min detections"
                leftSection={<IconEye size={16} />}
                value={minDetections}
                onChange={setMinDetections}
                min={0}
                max={50}
              />
            </Grid.Col>

            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <Group>
                <Switch
                  label="Has detections only"
                  checked={hasDetectionsOnly}
                  onChange={(e) =>
                    setHasDetectionsOnly(e.currentTarget.checked)
                  }
                />
              </Group>
            </Grid.Col>
          </Grid>
        </Stack>
      </Card>

      {/* Stats */}
      {photosData && (
        <Group gap="md">
          <Paper p="sm" withBorder>
            <Group gap="xs">
              <IconPhoto size={18} color="var(--mantine-color-blue-6)" />
              <Text size="sm">
                <Text span fw={600}>
                  {photosData.total.toLocaleString()}
                </Text>{" "}
                total photos
              </Text>
            </Group>
          </Paper>

          {filteredPhotos &&
            filteredPhotos.length !== photosData.photos.length && (
              <Paper p="sm" withBorder>
                <Group gap="xs">
                  <IconFilter size={18} color="var(--mantine-color-orange-6)" />
                  <Text size="sm">
                    <Text span fw={600}>
                      {filteredPhotos.length}
                    </Text>{" "}
                    filtered results
                  </Text>
                </Group>
              </Paper>
            )}
        </Group>
      )}

      {/* Photo Grid */}
      {photosLoading ? (
        <Grid>
          {Array.from({ length: PAGE_SIZE }).map((_, index) => (
            <Grid.Col
              key={index}
              span={{ base: 12, xs: 6, sm: 4, md: 3, lg: 2.4 }}
            >
              <Card shadow="sm" padding="sm" radius="md" withBorder>
                <Card.Section>
                  <Skeleton height={200} />
                </Card.Section>
                <Stack gap="xs" mt="sm">
                  <Skeleton height={16} />
                  <Skeleton height={12} width="60%" />
                </Stack>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      ) : filteredPhotos && filteredPhotos.length > 0 ? (
        <>
          <Grid>
            {filteredPhotos.map((photo) => (
              <Grid.Col
                key={photo.id}
                span={{ base: 12, xs: 6, sm: 4, md: 3, lg: 2.4 }}
              >
                <Card
                  shadow="sm"
                  padding="sm"
                  radius="md"
                  withBorder
                  style={{
                    cursor: "pointer",
                    transition: "transform 0.2s ease",
                  }}
                  onClick={() => handlePhotoClick(photo.id)}
                  className="hover-lift"
                >
                  <Card.Section>
                    <Image
                      src={getImageUrl(photo.filepath)}
                      alt={photo.filename}
                      height={200}
                      fit="cover"
                      fallbackSrc="/placeholder-image.png"
                    />
                  </Card.Section>

                  <Stack gap="xs" mt="sm">
                    <Group justify="space-between" wrap="nowrap">
                      <Text size="sm" fw={500} truncate title={photo.filename}>
                        {photo.filename}
                      </Text>
                      <Tooltip label="View details">
                        <ActionIcon size="sm" variant="light" color="blue">
                          <IconZoomIn size={14} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>

                    <Group justify="space-between" wrap="nowrap">
                      <Text size="xs" c="dimmed">
                        <IconClock
                          size={12}
                          style={{ display: "inline", marginRight: 4 }}
                        />
                        {dayjs(photo.timestamp).format("MMM D, HH:mm")}
                      </Text>

                      {photo.detection_count > 0 && (
                        <Badge size="sm" variant="light" color="green">
                          {photo.detection_count}{" "}
                          {photo.detection_count === 1
                            ? "detection"
                            : "detections"}
                        </Badge>
                      )}
                    </Group>

                    {photo.detections.length > 0 && (
                      <Group gap={4}>
                        {photo.detections.slice(0, 3).map((detection) => (
                          <Badge
                            key={detection.id}
                            size="xs"
                            variant="dot"
                            color="blue"
                            title={`${detection.class_name} (${(
                              detection.confidence * 100
                            ).toFixed(0)}%)`}
                          >
                            {detection.class_name}
                          </Badge>
                        ))}
                        {photo.detections.length > 3 && (
                          <Badge size="xs" variant="outline" color="gray">
                            +{photo.detections.length - 3}
                          </Badge>
                        )}
                      </Group>
                    )}
                  </Stack>
                </Card>
              </Grid.Col>
            ))}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Center>
              <Pagination
                value={page}
                onChange={setPage}
                total={totalPages}
                size="sm"
                withEdges
              />
            </Center>
          )}
        </>
      ) : (
        <Center py="xl">
          <Stack align="center" gap="md">
            <IconCamera size={48} color="var(--mantine-color-gray-5)" />
            <Stack align="center" gap="xs">
              <Text size="lg" fw={500} c="dimmed">
                No photos found
              </Text>
              <Text size="sm" c="dimmed" ta="center">
                {search || hasDetectionsOnly || minDetections
                  ? "Try adjusting your filters to see more results"
                  : "Photos will appear here once the camera starts capturing"}
              </Text>
            </Stack>
          </Stack>
        </Center>
      )}

      {/* Photo Detail Modal */}
      <Modal
        opened={modalOpened}
        onClose={handleModalClose}
        title={selectedPhoto?.filename || "Photo Details"}
        size="xl"
        centered
      >
        {photoLoading ? (
          <Center py="xl">
            <Loader size="lg" />
          </Center>
        ) : selectedPhoto ? (
          <Stack gap="md">
            {/* Image */}
            <Box pos="relative">
              <Image
                src={getImageUrl(selectedPhoto.filepath)}
                alt={selectedPhoto.filename}
                fit="contain"
                mah={500}
                fallbackSrc="/placeholder-image.png"
              />
            </Box>

            {/* Photo Info */}
            <Paper p="md" withBorder>
              <Grid>
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="sm" c="dimmed">
                      Filename
                    </Text>
                    <Text size="sm" fw={500}>
                      {selectedPhoto.filename}
                    </Text>
                  </Stack>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="sm" c="dimmed">
                      Timestamp
                    </Text>
                    <Text size="sm" fw={500}>
                      {dayjs(selectedPhoto.timestamp).format(
                        "MMMM D, YYYY at h:mm:ss A"
                      )}
                    </Text>
                  </Stack>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="sm" c="dimmed">
                      Dimensions
                    </Text>
                    <Text size="sm" fw={500}>
                      {selectedPhoto.width} × {selectedPhoto.height} px
                    </Text>
                  </Stack>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="sm" c="dimmed">
                      Detections
                    </Text>
                    <Text size="sm" fw={500}>
                      {selectedPhoto.detection_count}{" "}
                      {selectedPhoto.detection_count === 1
                        ? "object"
                        : "objects"}
                    </Text>
                  </Stack>
                </Grid.Col>
              </Grid>
            </Paper>

            {/* Detections */}
            {selectedPhoto.detections.length > 0 && (
              <Paper p="md" withBorder>
                <Stack gap="md">
                  <Text size="sm" fw={600}>
                    Detected Objects
                  </Text>
                  <Stack gap="sm">
                    {selectedPhoto.detections.map((detection) => (
                      <Group
                        key={detection.id}
                        justify="space-between"
                        wrap="nowrap"
                      >
                        <Group gap="sm">
                          <Badge variant="light" color="blue">
                            {detection.class_name}
                          </Badge>
                          <Text size="sm">
                            {(detection.confidence * 100).toFixed(1)}%
                            confidence
                          </Text>
                        </Group>
                        <Text size="xs" c="dimmed">
                          {Math.round(
                            detection.bbox.width * selectedPhoto.width
                          )}{" "}
                          ×{" "}
                          {Math.round(
                            detection.bbox.height * selectedPhoto.height
                          )}{" "}
                          px
                        </Text>
                      </Group>
                    ))}
                  </Stack>
                </Stack>
              </Paper>
            )}

            {/* Actions */}
            <Group justify="flex-end">
              <Button
                variant="light"
                leftSection={<IconDownload size={16} />}
                onClick={() => {
                  const link = document.createElement("a");
                  link.href = getImageUrl(selectedPhoto.filepath);
                  link.download = selectedPhoto.filename;
                  link.click();
                }}
              >
                Download
              </Button>
            </Group>
          </Stack>
        ) : null}
      </Modal>

      <style>{`
        .hover-lift:hover {
          transform: translateY(-4px);
          box-shadow: var(--mantine-shadow-md);
        }
      `}</style>
    </Stack>
  );
}
