import { Button, ButtonProps } from '@chakra-ui/react';
import { motion } from 'framer-motion';

const MotionButton = motion(Button);

type GradientButtonProps = Omit<ButtonProps, 'transition' | 'onAnimationStart' | 'onDragStart' | 'onDragEnd' | 'onDrag'>;

export function GradientButton({ children, ...rest }: GradientButtonProps) {
  return (
    <MotionButton
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      px={6}
      py={3}
      rounded="full"
      fontWeight="semibold"
      color="white"
      bgGradient="linear(to-r, purple.500, pink.500)"
      _hover={{ shadow: 'lg', bgGradient: 'linear(to-r, purple.600, pink.600)' }}
      {...rest}
    >
      {children}
    </MotionButton>
  );
}
