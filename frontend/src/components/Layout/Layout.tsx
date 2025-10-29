import { AppShell, Group, Title, ActionIcon, useMantineColorScheme, Burger, NavLink, Stack, Text, Badge } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconSun, IconMoon, IconHome, IconPhoto, IconEye, IconCamera, IconVideo } from '@tabler/icons-react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useStats } from '../../api/hooks';
import classes from './Layout.module.css';

export default function Layout() {
  const [opened, { toggle, close }] = useDisclosure();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const location = useLocation();
  const navigate = useNavigate();
  const { data: stats } = useStats();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: IconHome },
    { path: '/live', label: 'Live View', icon: IconVideo },
    { path: '/photos', label: 'Photos', icon: IconPhoto },
    { path: '/detections', label: 'Detections', icon: IconEye },
  ];

  return (
    <AppShell
      header={{ height: 70 }}
      navbar={{
        width: 280,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <IconCamera size={32} color="var(--mantine-color-green-6)" stroke={2} />
            <Title order={2} size="h3" c="green">Pi Yard Tracker</Title>
          </Group>
          
          <ActionIcon
            onClick={() => toggleColorScheme()}
            variant="default"
            size="lg"
            aria-label="Toggle color scheme"
          >
            {colorScheme === 'dark' ? <IconSun size={20} /> : <IconMoon size={20} />}
          </ActionIcon>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <AppShell.Section grow>
          <Stack gap="xs">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                label={item.label}
                leftSection={<item.icon size={20} stroke={1.5} />}
                active={location.pathname === item.path}
                onClick={() => {
                  navigate(item.path);
                  close();
                }}
                variant="filled"
              />
            ))}
          </Stack>
        </AppShell.Section>

        {stats && (
          <AppShell.Section>
            <Stack gap="xs" p="md" className={classes.statsSection}>
              <Text size="xs" fw={700} tt="uppercase" c="dimmed">
                System Stats
              </Text>
              <Group justify="space-between">
                <Text size="sm">Total Photos</Text>
                <Badge variant="light" color="blue">{stats.total_photos.toLocaleString()}</Badge>
              </Group>
              <Group justify="space-between">
                <Text size="sm">Detections</Text>
                <Badge variant="light" color="green">{stats.total_detections.toLocaleString()}</Badge>
              </Group>
              <Group justify="space-between">
                <Text size="sm">Classes</Text>
                <Badge variant="light" color="orange">{stats.unique_classes}</Badge>
              </Group>
            </Stack>
          </AppShell.Section>
        )}
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
