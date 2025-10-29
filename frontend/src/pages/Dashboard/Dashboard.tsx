import { useState } from 'react';
import { Grid, Card, Title, Text, Group, Stack, RingProgress, Badge, Loader, Alert, SimpleGrid, Paper, SegmentedControl } from '@mantine/core';
import { IconPhoto, IconEye, IconTags, IconCamera, IconClock, IconInfoCircle, IconTimeline } from '@tabler/icons-react';
import { BarChart, LineChart, DonutChart } from '@mantine/charts';
import { useStats, useDetectionClasses, usePhotos } from '../../api/hooks';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState('24h');
  const [chartType, setChartType] = useState('hourly');
  
  const { data: stats, isLoading: statsLoading, error: statsError } = useStats();
  const { data: classes, isLoading: classesLoading } = useDetectionClasses();
  const { data: recentPhotos, isLoading: photosLoading } = usePhotos({ limit: 5, has_detections: true });

  if (statsError) {
    return (
      <Alert icon={<IconInfoCircle size={16} />} title="Connection Error" color="red">
        Unable to connect to the API. Please ensure the backend server is running.
      </Alert>
    );
  }

  if (statsLoading) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader size="xl" />
        <Text c="dimmed">Loading dashboard...</Text>
      </Stack>
    );
  }

  if (!stats) {
    return null;
  }

  const detectionRate = stats.total_photos > 0 
    ? Math.round((stats.total_detections / stats.total_photos) * 100) 
    : 0;

  const chartData = classes?.slice(0, 10).map(c => ({
    class: c.class_name,
    count: c.count,
  })) || [];

  // Mock timeline data - In real implementation, this would come from an API
  const generateTimelineData = () => {
    const now = dayjs();
    const data = [];
    const intervals = timeRange === '24h' ? 24 : timeRange === '7d' ? 7 : 30;
    const unit = timeRange === '24h' ? 'hour' : 'day';
    
    for (let i = intervals - 1; i >= 0; i--) {
      const time = now.subtract(i, unit);
      const randomDetections = Math.floor(Math.random() * 15);
      const randomPhotos = Math.floor(Math.random() * 25) + 5;
      
      data.push({
        time: time.format(timeRange === '24h' ? 'HH:mm' : 'MMM D'),
        fullTime: time.format('YYYY-MM-DD HH:mm'),
        detections: randomDetections,
        photos: randomPhotos,
        activity: randomDetections > 10 ? 'High' : randomDetections > 5 ? 'Medium' : 'Low',
      });
    }
    return data;
  };

  const timelineData = generateTimelineData();

  // Mock detection activity by hour (for heatmap-style visualization)
  const generateHourlyActivity = () => {
    const hours = [];
    for (let i = 0; i < 24; i++) {
      const activity = Math.floor(Math.random() * 100);
      hours.push({
        hour: i.toString().padStart(2, '0') + ':00',
        activity,
        level: activity > 70 ? 'High' : activity > 30 ? 'Medium' : 'Low',
      });
    }
    return hours;
  };

  const hourlyActivity = generateHourlyActivity();

  // Donut chart data for detection distribution
  const donutData = classes?.slice(0, 5).map((cls, index) => ({
    name: cls.class_name,
    value: cls.count,
    color: ['green.6', 'blue.6', 'orange.6', 'red.6', 'violet.6'][index % 5],
  })) || [];

  return (
    <Stack gap="lg">
      <div>
        <Title order={1} size="h2">Wildlife Monitoring Dashboard</Title>
        <Text c="dimmed" size="sm" mt={4}>
          Real-time detection statistics and activity timeline • Updates every 5 seconds
        </Text>
      </div>

      {/* Stats Cards */}
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md">
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed" fw={500}>Total Photos</Text>
              <IconPhoto size={20} color="var(--mantine-color-blue-6)" />
            </Group>
            <Text size="xl" fw={700}>{stats.total_photos.toLocaleString()}</Text>
            {stats.latest_photo_time && (
              <Text size="xs" c="dimmed">
                <IconClock size={12} style={{ display: 'inline', marginRight: 4 }} />
                Last: {dayjs(stats.latest_photo_time).fromNow()}
              </Text>
            )}
          </Stack>
        </Card>

        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed" fw={500}>Total Detections</Text>
              <IconEye size={20} color="var(--mantine-color-green-6)" />
            </Group>
            <Text size="xl" fw={700}>{stats.total_detections.toLocaleString()}</Text>
            <Text size="xs" c="dimmed">
              Avg: {stats.avg_detections_per_photo.toFixed(2)} per photo
            </Text>
          </Stack>
        </Card>

        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed" fw={500}>Unique Classes</Text>
              <IconTags size={20} color="var(--mantine-color-orange-6)" />
            </Group>
            <Text size="xl" fw={700}>{stats.unique_classes}</Text>
            {stats.most_detected_class && (
              <Badge variant="light" color="orange" size="sm">
                Most: {stats.most_detected_class}
              </Badge>
            )}
          </Stack>
        </Card>

        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed" fw={500}>Detection Rate</Text>
              <IconCamera size={20} color="var(--mantine-color-violet-6)" />
            </Group>
            <Group align="flex-end" gap="xs">
              <Text size="xl" fw={700}>{detectionRate}%</Text>
              <Text size="sm" c="dimmed" mb={2}>of photos</Text>
            </Group>
            <RingProgress
              size={60}
              thickness={6}
              sections={[{ value: detectionRate, color: 'violet' }]}
              label={
                <Text size="xs" ta="center" fw={700}>
                  {detectionRate}%
                </Text>
              }
            />
          </Stack>
        </Card>
      </SimpleGrid>

      {/* Timeline Section */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group justify="space-between">
            <Group gap="md">
              <IconTimeline size={20} color="var(--mantine-color-blue-6)" />
              <Title order={3} size="h4">Activity Timeline</Title>
            </Group>
            <Group gap="md">
              <SegmentedControl
                value={timeRange}
                onChange={setTimeRange}
                data={[
                  { label: '24 Hours', value: '24h' },
                  { label: '7 Days', value: '7d' },
                  { label: '30 Days', value: '30d' },
                ]}
                size="sm"
              />
              <SegmentedControl
                value={chartType}
                onChange={setChartType}
                data={[
                  { label: 'Timeline', value: 'hourly' },
                  { label: 'Activity Map', value: 'heatmap' },
                ]}
                size="sm"
              />
            </Group>
          </Group>

          {chartType === 'hourly' ? (
            <LineChart
              h={300}
              data={timelineData}
              dataKey="time"
              series={[
                { name: 'detections', color: 'green.6', label: 'Detections' },
                { name: 'photos', color: 'blue.6', label: 'Photos' },
              ]}
              curveType="natural"
              tickLine="xy"
              gridAxis="xy"
              withLegend
              legendProps={{ verticalAlign: 'top', height: 50 }}
            />
          ) : (
            <Grid>
              {hourlyActivity.map((hour) => (
                <Grid.Col key={hour.hour} span={1}>
                  <Paper
                    p="xs"
                    style={{
                      backgroundColor: 
                        hour.level === 'High' ? 'var(--mantine-color-green-1)' :
                        hour.level === 'Medium' ? 'var(--mantine-color-yellow-1)' :
                        'var(--mantine-color-gray-1)',
                      border: `1px solid ${
                        hour.level === 'High' ? 'var(--mantine-color-green-3)' :
                        hour.level === 'Medium' ? 'var(--mantine-color-yellow-3)' :
                        'var(--mantine-color-gray-3)'
                      }`,
                      borderRadius: 4,
                      textAlign: 'center',
                    }}
                  >
                    <Text size="xs" fw={500}>{hour.hour}</Text>
                    <Text size="xs" c="dimmed">{hour.activity}%</Text>
                  </Paper>
                </Grid.Col>
              ))}
            </Grid>
          )}

          <Text size="xs" c="dimmed">
            {chartType === 'hourly' 
              ? `Activity over the last ${timeRange === '24h' ? '24 hours' : timeRange === '7d' ? '7 days' : '30 days'}`
              : 'Detection activity by hour of day (24-hour format)'
            }
          </Text>
        </Stack>
      </Card>

      <Grid>
        {/* Detection Classes Chart */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Stack gap="md">
              <div>
                <Title order={3} size="h4">Top Detected Classes</Title>
                <Text size="sm" c="dimmed">Most frequently detected objects</Text>
              </div>
              
              {classesLoading ? (
                <Stack align="center" justify="center" h={300}>
                  <Loader />
                </Stack>
              ) : chartData.length > 0 ? (
                <BarChart
                  h={300}
                  data={chartData}
                  dataKey="class"
                  series={[{ name: 'count', color: 'green.6', label: 'Detections' }]}
                  tickLine="y"
                  gridAxis="y"
                />
              ) : (
                <Stack align="center" justify="center" h={300}>
                  <Text c="dimmed">No detections yet</Text>
                </Stack>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* Detection Distribution & Recent Activity */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Stack gap="md">
            {/* Detection Distribution Donut Chart */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Stack gap="md">
                <div>
                  <Title order={3} size="h4">Detection Distribution</Title>
                  <Text size="sm" c="dimmed">Breakdown by class</Text>
                </div>
                
                {donutData.length > 0 ? (
                  <DonutChart
                    data={donutData}
                    tooltipDataSource="segment"
                    mx="auto"
                    size={160}
                    thickness={30}
                  />
                ) : (
                  <Stack align="center" justify="center" h={160}>
                    <Text c="dimmed" size="sm">No data available</Text>
                  </Stack>
                )}
              </Stack>
            </Card>

            {/* Recent Activity */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Stack gap="md">
                <div>
                  <Title order={3} size="h4">Recent Activity</Title>
                  <Text size="sm" c="dimmed">Latest detections</Text>
                </div>
                
                {photosLoading ? (
                  <Stack align="center" justify="center" h={200}>
                    <Loader size="sm" />
                  </Stack>
                ) : recentPhotos && recentPhotos.photos.length > 0 ? (
                  <Stack gap="sm">
                    {recentPhotos.photos.map((photo) => (
                      <Paper key={photo.id} p="sm" withBorder>
                        <Stack gap={4}>
                          <Group justify="space-between" wrap="nowrap">
                            <Text size="sm" fw={500} truncate>
                              {photo.filename}
                            </Text>
                            <Badge size="sm" variant="light" color="green">
                              {photo.detection_count}
                            </Badge>
                          </Group>
                          <Text size="xs" c="dimmed">
                            {dayjs(photo.timestamp).fromNow()}
                          </Text>
                          <Group gap={4}>
                            {photo.detections.slice(0, 2).map((det) => (
                              <Badge key={det.id} size="xs" variant="dot" color="blue">
                                {det.class_name} ({(det.confidence * 100).toFixed(0)}%)
                              </Badge>
                            ))}
                            {photo.detections.length > 2 && (
                              <Badge size="xs" variant="outline" color="gray">
                                +{photo.detections.length - 2}
                              </Badge>
                            )}
                          </Group>
                        </Stack>
                      </Paper>
                    ))}
                  </Stack>
                ) : (
                  <Stack align="center" justify="center" h={200}>
                    <Text c="dimmed" size="sm">No recent activity</Text>
                  </Stack>
                )}
              </Stack>
            </Card>
          </Stack>
        </Grid.Col>
      </Grid>

      {stats.active_session_id && (
        <Alert icon={<IconCamera size={16} />} title="Active Session" color="green" variant="light">
          Session #{stats.active_session_id} is currently running
        </Alert>
      )}
    </Stack>
  );
}
