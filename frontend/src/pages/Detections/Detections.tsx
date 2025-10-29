import { useState } from 'react';
import {
  Stack,
  Title,
  Text,
  Table,
  Card,
  Group,
  Badge,
  Button,
  Modal,
  Pagination,
  TextInput,
  Select,
  ActionIcon,
  Paper,
  Skeleton,
  Alert,
  Center,
  Loader,
  Tooltip,
  Image,
  Grid,
  RangeSlider,
  Box,
  ScrollArea,
} from '@mantine/core';
import {
  IconSearch,
  IconFilter,
  IconX,
  IconEye,
  IconZoomIn,
  IconInfoCircle,
  IconSortAscending,
  IconSortDescending,
  IconTarget,
} from '@tabler/icons-react';
import { useDisclosure } from '@mantine/hooks';
import { useDetections, useDetectionClasses, usePhoto } from '../../api/hooks';
import dayjs from 'dayjs';

export default function Detections() {
  const [page, setPage] = useState(1);
  const [classFilter, setClassFilter] = useState<string>('');
  const [confidenceRange, setConfidenceRange] = useState<[number, number]>([0, 100]);
  const [sortField, setSortField] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [search, setSearch] = useState('');
  const [selectedDetectionId, setSelectedDetectionId] = useState<number | null>(null);
  const [selectedPhotoId, setSelectedPhotoId] = useState<number | null>(null);
  const [modalOpened, { open: openModal, close: closeModal }] = useDisclosure(false);

  const PAGE_SIZE = 50;

  // Fetch detections with current filters
  const {
    data: detectionsData,
    isLoading: detectionsLoading,
    error: detectionsError,
  } = useDetections({
    page,
    limit: PAGE_SIZE,
    class_name: classFilter || undefined,
    min_confidence: confidenceRange[0] / 100,
    max_confidence: confidenceRange[1] / 100,
  });

  // Fetch detection classes for filter dropdown
  const { data: classes } = useDetectionClasses();

  // Fetch selected photo details
  const { data: selectedPhoto, isLoading: photoLoading } = usePhoto(selectedPhotoId);

  const handleDetectionClick = (detectionId: number, photoId: number) => {
    setSelectedDetectionId(detectionId);
    setSelectedPhotoId(photoId);
    openModal();
  };

  const handleModalClose = () => {
    closeModal();
    setSelectedDetectionId(null);
    setSelectedPhotoId(null);
  };

  const filteredDetections = detectionsData?.detections.filter((detection) => {
    if (search && !detection.class_name.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    return true;
  });

  const totalPages = detectionsData ? Math.ceil(detectionsData.total / PAGE_SIZE) : 0;

  const getImageUrl = (filepath: string) => {
    const filename = filepath.split('/').pop();
    return `http://localhost:8000/photos/image/${filename}`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'green';
    if (confidence >= 0.6) return 'yellow';
    if (confidence >= 0.4) return 'orange';
    return 'red';
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  if (detectionsError) {
    return (
      <Alert icon={<IconInfoCircle size={16} />} title="Connection Error" color="red">
        Unable to load detections. Please ensure the backend server is running.
      </Alert>
    );
  }

  return (
    <Stack gap="lg">
      {/* Header */}
      <div>
        <Title order={1} size="h2">Detection Records</Title>
        <Text c="dimmed" size="sm" mt={4}>
          Detailed view of all object detections with filtering and analysis
        </Text>
      </div>

      {/* Filters */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group justify="space-between">
            <Text fw={600} size="sm">Advanced Filters</Text>
            <Button
              variant="light"
              size="xs"
              leftSection={<IconX size={14} />}
              onClick={() => {
                setSearch('');
                setClassFilter('');
                setConfidenceRange([0, 100]);
                setSortField('created_at');
                setSortOrder('desc');
                setPage(1);
              }}
            >
              Clear All
            </Button>
          </Group>

          <Grid>
            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <TextInput
                placeholder="Search by class name..."
                leftSection={<IconSearch size={16} />}
                value={search}
                onChange={(e) => setSearch(e.currentTarget.value)}
              />
            </Grid.Col>

            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <Select
                placeholder="Filter by class"
                data={[
                  { value: '', label: 'All Classes' },
                  ...(classes?.map((cls) => ({
                    value: cls.class_name,
                    label: `${cls.class_name} (${cls.count})`
                  })) || [])
                ]}
                value={classFilter}
                onChange={(value) => setClassFilter(value || '')}
                searchable
                clearable
              />
            </Grid.Col>

            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <Select
                placeholder="Sort by"
                data={[
                  { value: 'created_at', label: 'Date' },
                  { value: 'confidence', label: 'Confidence' },
                  { value: 'class_name', label: 'Class Name' },
                  { value: 'photo_id', label: 'Photo ID' },
                ]}
                value={sortField}
                onChange={(value) => setSortField(value || 'created_at')}
              />
            </Grid.Col>

            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
              <Stack gap="xs">
                <Text size="sm" fw={500}>Confidence Range</Text>
                <RangeSlider
                  value={confidenceRange}
                  onChange={setConfidenceRange}
                  min={0}
                  max={100}
                  step={5}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 25, label: '25%' },
                    { value: 50, label: '50%' },
                    { value: 75, label: '75%' },
                    { value: 100, label: '100%' },
                  ]}
                />
                <Text size="xs" c="dimmed" ta="center">
                  {confidenceRange[0]}% - {confidenceRange[1]}%
                </Text>
              </Stack>
            </Grid.Col>
          </Grid>
        </Stack>
      </Card>

      {/* Stats */}
      {detectionsData && (
        <Group gap="md">
          <Paper p="sm" withBorder>
            <Group gap="xs">
              <IconTarget size={18} color="var(--mantine-color-green-6)" />
              <Text size="sm">
                <Text span fw={600}>{detectionsData.total.toLocaleString()}</Text> total detections
              </Text>
            </Group>
          </Paper>
          
          {filteredDetections && filteredDetections.length !== detectionsData.detections.length && (
            <Paper p="sm" withBorder>
              <Group gap="xs">
                <IconFilter size={18} color="var(--mantine-color-orange-6)" />
                <Text size="sm">
                  <Text span fw={600}>{filteredDetections.length}</Text> filtered results
                </Text>
              </Group>
            </Paper>
          )}

          {classes && (
            <Paper p="sm" withBorder>
              <Group gap="xs">
                <IconEye size={18} color="var(--mantine-color-blue-6)" />
                <Text size="sm">
                  <Text span fw={600}>{classes.length}</Text> unique classes
                </Text>
              </Group>
            </Paper>
          )}
        </Group>
      )}

      {/* Detections Table */}
      {detectionsLoading ? (
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Stack gap="md">
            {Array.from({ length: 10 }).map((_, index) => (
              <Group key={index} justify="space-between">
                <Group gap="md">
                  <Skeleton height={40} width={60} />
                  <Stack gap="xs">
                    <Skeleton height={16} width={120} />
                    <Skeleton height={12} width={80} />
                  </Stack>
                </Group>
                <Skeleton height={20} width={60} />
              </Group>
            ))}
          </Stack>
        </Card>
      ) : filteredDetections && filteredDetections.length > 0 ? (
        <>
          <Card shadow="sm" padding={0} radius="md" withBorder>
            <ScrollArea>
              <Table highlightOnHover striped>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>
                      <Button
                        variant="transparent"
                        size="xs"
                        rightSection={
                          sortField === 'class_name' ? (
                            sortOrder === 'asc' ? <IconSortAscending size={14} /> : <IconSortDescending size={14} />
                          ) : null
                        }
                        onClick={() => handleSort('class_name')}
                      >
                        Class
                      </Button>
                    </Table.Th>
                    <Table.Th>
                      <Button
                        variant="transparent"
                        size="xs"
                        rightSection={
                          sortField === 'confidence' ? (
                            sortOrder === 'asc' ? <IconSortAscending size={14} /> : <IconSortDescending size={14} />
                          ) : null
                        }
                        onClick={() => handleSort('confidence')}
                      >
                        Confidence
                      </Button>
                    </Table.Th>
                    <Table.Th>Bounding Box</Table.Th>
                    <Table.Th>
                      <Button
                        variant="transparent"
                        size="xs"
                        rightSection={
                          sortField === 'photo_id' ? (
                            sortOrder === 'asc' ? <IconSortAscending size={14} /> : <IconSortDescending size={14} />
                          ) : null
                        }
                        onClick={() => handleSort('photo_id')}
                      >
                        Photo
                      </Button>
                    </Table.Th>
                    <Table.Th>
                      <Button
                        variant="transparent"
                        size="xs"
                        rightSection={
                          sortField === 'created_at' ? (
                            sortOrder === 'asc' ? <IconSortAscending size={14} /> : <IconSortDescending size={14} />
                          ) : null
                        }
                        onClick={() => handleSort('created_at')}
                      >
                        Detected At
                      </Button>
                    </Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {filteredDetections.map((detection) => (
                    <Table.Tr key={detection.id}>
                      <Table.Td>
                        <Group gap="xs">
                          <Badge
                            variant="light"
                            color={getConfidenceColor(detection.confidence)}
                            size="md"
                          >
                            {detection.class_name}
                          </Badge>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Text size="sm" fw={600}>
                            {(detection.confidence * 100).toFixed(1)}%
                          </Text>
                          <div
                            style={{
                              width: 60,
                              height: 8,
                              backgroundColor: 'var(--mantine-color-gray-2)',
                              borderRadius: 4,
                              overflow: 'hidden'
                            }}
                          >
                            <div
                              style={{
                                width: `${detection.confidence * 100}%`,
                                height: '100%',
                                backgroundColor: `var(--mantine-color-${getConfidenceColor(detection.confidence)}-6)`,
                                transition: 'width 0.3s ease'
                              }}
                            />
                          </div>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Text size="xs" c="dimmed">
                          {Math.round(detection.bbox.width * 100)}% × {Math.round(detection.bbox.height * 100)}%
                          <br />
                          @({Math.round(detection.bbox.x_center * 100)}, {Math.round(detection.bbox.y_center * 100)})
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Badge variant="outline" size="sm">
                            #{detection.photo_id}
                          </Badge>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">
                          {dayjs(detection.created_at).format('MMM D, HH:mm')}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {dayjs(detection.created_at).fromNow()}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Tooltip label="View photo with detection">
                            <ActionIcon
                              size="sm"
                              variant="light"
                              color="blue"
                              onClick={() => handleDetectionClick(detection.id, detection.photo_id)}
                            >
                              <IconZoomIn size={14} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </ScrollArea>
          </Card>

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
            <IconTarget size={48} color="var(--mantine-color-gray-5)" />
            <Stack align="center" gap="xs">
              <Text size="lg" fw={500} c="dimmed">
                No detections found
              </Text>
              <Text size="sm" c="dimmed" ta="center">
                {search || classFilter || confidenceRange[0] > 0 || confidenceRange[1] < 100
                  ? 'Try adjusting your filters to see more results'
                  : 'Detections will appear here once objects are detected in photos'}
              </Text>
            </Stack>
          </Stack>
        </Center>
      )}

      {/* Detection Detail Modal */}
      <Modal
        opened={modalOpened}
        onClose={handleModalClose}
        title="Detection Details"
        size="xl"
        centered
      >
        {photoLoading ? (
          <Center py="xl">
            <Loader size="lg" />
          </Center>
        ) : selectedPhoto ? (
          <Stack gap="md">
            {/* Photo with Detection Overlay */}
            <Box pos="relative">
              <Image
                src={getImageUrl(selectedPhoto.filepath)}
                alt={selectedPhoto.filename}
                fit="contain"
                mah={400}
                fallbackSrc="/placeholder-image.png"
                onLoad={(e) => {
                  // Draw bounding boxes on the image
                  const canvas = document.createElement('canvas');
                  const ctx = canvas.getContext('2d');
                  const img = e.currentTarget as HTMLImageElement;
                  
                  if (ctx && selectedDetectionId) {
                    const detection = selectedPhoto.detections.find(d => d.id === selectedDetectionId);
                    if (detection) {
                      canvas.width = img.naturalWidth;
                      canvas.height = img.naturalHeight;
                      
                      // Draw the image
                      ctx.drawImage(img, 0, 0);
                      
                      // Draw bounding box
                      const bbox = detection.bbox;
                      const x = bbox.x_min * canvas.width;
                      const y = bbox.y_min * canvas.height;
                      const width = bbox.width * canvas.width;
                      const height = bbox.height * canvas.height;
                      
                      ctx.strokeStyle = '#00d4aa';
                      ctx.lineWidth = 3;
                      ctx.strokeRect(x, y, width, height);
                      
                      // Draw label
                      ctx.fillStyle = '#00d4aa';
                      ctx.fillRect(x, y - 25, ctx.measureText(detection.class_name).width + 10, 25);
                      ctx.fillStyle = 'white';
                      ctx.font = '16px Arial';
                      ctx.fillText(detection.class_name, x + 5, y - 5);
                      
                      // Replace image with canvas
                      img.src = canvas.toDataURL();
                    }
                  }
                }}
              />
            </Box>

            {/* Detection Information */}
            {selectedDetectionId && (
              <>
                {(() => {
                  const detection = selectedPhoto.detections.find(d => d.id === selectedDetectionId);
                  if (!detection) return null;
                  
                  return (
                    <Paper p="md" withBorder>
                      <Grid>
                        <Grid.Col span={6}>
                          <Stack gap="xs">
                            <Text size="sm" c="dimmed">Class</Text>
                            <Badge size="lg" variant="light" color={getConfidenceColor(detection.confidence)}>
                              {detection.class_name}
                            </Badge>
                          </Stack>
                        </Grid.Col>
                        <Grid.Col span={6}>
                          <Stack gap="xs">
                            <Text size="sm" c="dimmed">Confidence</Text>
                            <Group gap="xs">
                              <Text size="lg" fw={600}>
                                {(detection.confidence * 100).toFixed(1)}%
                              </Text>
                              <div
                                style={{
                                  width: 100,
                                  height: 12,
                                  backgroundColor: 'var(--mantine-color-gray-2)',
                                  borderRadius: 6,
                                  overflow: 'hidden'
                                }}
                              >
                                <div
                                  style={{
                                    width: `${detection.confidence * 100}%`,
                                    height: '100%',
                                    backgroundColor: `var(--mantine-color-${getConfidenceColor(detection.confidence)}-6)`,
                                  }}
                                />
                              </div>
                            </Group>
                          </Stack>
                        </Grid.Col>
                        <Grid.Col span={6}>
                          <Stack gap="xs">
                            <Text size="sm" c="dimmed">Bounding Box</Text>
                            <Text size="sm" fw={500}>
                              {Math.round(detection.bbox.width * selectedPhoto.width)} × {Math.round(detection.bbox.height * selectedPhoto.height)} px
                            </Text>
                            <Text size="xs" c="dimmed">
                              Position: ({Math.round(detection.bbox.x_center * selectedPhoto.width)}, {Math.round(detection.bbox.y_center * selectedPhoto.height)})
                            </Text>
                          </Stack>
                        </Grid.Col>
                        <Grid.Col span={6}>
                          <Stack gap="xs">
                            <Text size="sm" c="dimmed">Detected At</Text>
                            <Text size="sm" fw={500}>
                              {dayjs(detection.created_at).format('MMMM D, YYYY at h:mm:ss A')}
                            </Text>
                            <Text size="xs" c="dimmed">
                              {dayjs(detection.created_at).fromNow()}
                            </Text>
                          </Stack>
                        </Grid.Col>
                      </Grid>
                    </Paper>
                  );
                })()}
              </>
            )}

            {/* Photo Information */}
            <Paper p="md" withBorder>
              <Stack gap="xs">
                <Text size="sm" fw={600}>Photo Information</Text>
                <Grid>
                  <Grid.Col span={6}>
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Filename</Text>
                      <Text size="sm" fw={500}>{selectedPhoto.filename}</Text>
                    </Group>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Dimensions</Text>
                      <Text size="sm" fw={500}>
                        {selectedPhoto.width} × {selectedPhoto.height} px
                      </Text>
                    </Group>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Total Detections</Text>
                      <Badge size="sm" variant="light" color="green">
                        {selectedPhoto.detection_count}
                      </Badge>
                    </Group>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Photo ID</Text>
                      <Text size="sm" fw={500}>#{selectedPhoto.id}</Text>
                    </Group>
                  </Grid.Col>
                </Grid>
              </Stack>
            </Paper>

            {/* All Detections in This Photo */}
            {selectedPhoto.detections.length > 1 && (
              <Paper p="md" withBorder>
                <Stack gap="md">
                  <Text size="sm" fw={600}>Other Detections in This Photo</Text>
                  <Stack gap="sm">
                    {selectedPhoto.detections
                      .filter(d => d.id !== selectedDetectionId)
                      .map((detection) => (
                        <Group key={detection.id} justify="space-between">
                          <Group gap="sm">
                            <Badge variant="light" color={getConfidenceColor(detection.confidence)}>
                              {detection.class_name}
                            </Badge>
                            <Text size="sm">
                              {(detection.confidence * 100).toFixed(1)}% confidence
                            </Text>
                          </Group>
                          <Button
                            size="xs"
                            variant="light"
                            onClick={() => setSelectedDetectionId(detection.id)}
                          >
                            View
                          </Button>
                        </Group>
                      ))}
                  </Stack>
                </Stack>
              </Paper>
            )}
          </Stack>
        ) : null}
      </Modal>
    </Stack>
  );
}