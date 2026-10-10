import { Box, Button, Flex, HStack, Link, Text } from '@chakra-ui/react';
import { NavLink, Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface NavItem {
  to: string;
  label: string;
}

const PUBLIC_ITEMS: NavItem[] = [
  { to: '/', label: 'Roast' },
  { to: '/gallery', label: 'Gallery' },
];

const MEMBER_ITEMS: NavItem[] = [
  { to: '/roasts', label: 'My roasts' },
  { to: '/dashboard', label: 'Dashboard' },
];

function NavItemLink({ to, label }: NavItem) {
  return (
    <Link
      as={NavLink}
      to={to}
      end={to === '/'}
      px={3}
      py={1}
      rounded="full"
      fontWeight="medium"
      color="gray.700"
      _hover={{ textDecoration: 'none', bg: 'purple.50' }}
      _activeLink={{ bg: 'purple.100', color: 'purple.700' }}
    >
      {label}
    </Link>
  );
}

export function NavBar() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate('/', { replace: true });
  };

  const items = isAuthenticated ? [...PUBLIC_ITEMS, ...MEMBER_ITEMS] : PUBLIC_ITEMS;

  return (
    <Box as="header" borderBottomWidth="1px" borderColor="blackAlpha.100" bg="whiteAlpha.900" position="sticky" top={0} zIndex={10}>
      <Flex as="nav" aria-label="Main" maxW="6xl" mx="auto" px={4} py={2} align="center" justify="space-between" wrap="wrap" gap={2}>
        <Link as={RouterLink} to="/" _hover={{ textDecoration: 'none' }}>
          <Text fontWeight="extrabold" bgGradient="linear(to-r, purple.500, pink.500)" bgClip="text">
            Team14-Roast
          </Text>
        </Link>
        <HStack spacing={1} wrap="wrap">
          {items.map((item) => (
            <NavItemLink key={item.to} {...item} />
          ))}
        </HStack>
        <HStack spacing={2}>
          {isLoading ? null : isAuthenticated ? (
            <>
              <Link as={RouterLink} to="/settings" fontSize="sm" color="gray.600" noOfLines={1} maxW="40">
                {user?.full_name || user?.email}
              </Link>
              <Button size="sm" variant="outline" onClick={handleLogout}>
                Log out
              </Button>
            </>
          ) : (
            <>
              <Button as={RouterLink} to="/login" size="sm" variant="ghost">
                Log in
              </Button>
              <Button as={RouterLink} to="/register" size="sm" colorScheme="purple">
                Sign up
              </Button>
            </>
          )}
        </HStack>
      </Flex>
    </Box>
  );
}
