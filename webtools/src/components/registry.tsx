import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  List,
  ListItem,
  Code,
  Grid,
  GridItem,
} from '@chakra-ui/react'
import type { RegistryEntry } from './data';

interface RegistryProps {
    registry: Record<string, RegistryEntry>;
}

function Registry(props: RegistryProps) {
    const { registry } = props;
    return (
        <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }} gap={6}>
            {Object.entries(registry).map(([key, entry]) => (
            <GridItem key={key}>
                <Box
                borderWidth="1px"
                borderRadius="md"
                p={4}
                bg="white"
                shadow="sm"
                h="100%"
                >
                <VStack align="start" gap={3}>
                    <Heading as="h3" size="md" color="blue.600">
                    {key}
                    </Heading>
                    
                    <HStack>
                    <Text fontWeight="semibold">Interface:</Text>
                    <Code>{entry.interface}</Code>
                    </HStack>
                    
                    <HStack>
                    <Text fontWeight="semibold">Functions:</Text>
                    <Code>[{entry.funcs.join(', ')}]</Code>
                    </HStack>
                    
                    <Box>
                    <Text fontWeight="semibold" mb={2}>Rules:</Text>
                    <List.Root>
                        {entry.rules.map((rule, index) => (
                        <ListItem key={index}>
                            <Code fontSize="sm">{rule}</Code>
                        </ListItem>
                        ))}
                    </List.Root>
                    </Box>
                </VStack>
                </Box>
            </GridItem>
            ))}
        </Grid>
    );
}

export default Registry